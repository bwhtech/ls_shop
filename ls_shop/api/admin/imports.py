# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Bulk product import: a downloadable spreadsheet template, and the importer that reads one back.

One spreadsheet row is one colour/size combination (a future SKU). Rows sharing a Product Title
become one product, created through the same catalog.create_product engine the single-product
dialog uses — this module never touches Item / Style Attribute Configurator directly. Price is a
create_product-level concept (one price for the whole product, not per size), so every row for one
product must agree on it.
"""

import frappe
from frappe import _
from frappe.utils.csvutils import read_csv_content
from frappe.utils.data import cstr, flt
from frappe.utils.xlsxutils import build_xlsx_response, read_xlsx_file_from_attached_file

from ls_shop.api.admin.catalog import create_product

TEMPLATE_HEADERS = [
	"Product Title",
	"Collection",
	"Color",
	"Size",
	"Compare at price",
	"Selling price",
	"Stock",
]

# Every field an importer accepts, in TEMPLATE_HEADERS order, with the synonyms an uploaded file's
# own header row is matched against (case/space/punctuation-insensitive) — see suggest_mapping().
FIELD_SYNONYMS = {
	"title": ["product title", "title", "product name", "name"],
	"collection": ["collection", "category", "item group"],
	"color": ["color", "colour"],
	"size": ["size"],
	"compare_at_price": ["compare at price", "mrp", "compare at", "list price"],
	"sale_price": ["selling price", "price", "sale price"],
	"stock": ["stock", "quantity", "qty", "stock quantity", "qty on hand"],
}
FIELD_LABELS = dict(zip(FIELD_SYNONYMS, TEMPLATE_HEADERS, strict=True))
REQUIRED_FIELDS = ["title", "collection", "color", "size"]

# Every product this importer creates uses this store's own Color/Size attributes — the same two
# create_product's own Trap 2 guard requires (generate_variants() depends on the exact name "Size").
OPTION_ATTRIBUTE = "Color"
SIZE_ATTRIBUTE = "Size"


def normalize_header(text):
	return "".join(ch for ch in cstr(text).strip().casefold() if ch.isalnum() or ch == " ").strip()


@frappe.whitelist()
def download_product_template():
	"""A ready-to-fill spreadsheet whose header row matches parse_and_validate() column for column."""
	frappe.has_permission("Item", ptype="create", throw=True)

	example_collection = frappe.db.get_value("Item Group", {"is_group": 0}) or "Apparel"
	example_rows = [
		["Cotton Oversized Tee", example_collection, "Black", "M", 1299, 999, 24],
		["Cotton Oversized Tee", example_collection, "Black", "L", 1299, 999, 18],
		["Cotton Oversized Tee", example_collection, "Sand", "M", 1299, 999, 12],
	]
	build_xlsx_response([TEMPLATE_HEADERS, *example_rows], "Product import template")


def read_uploaded_rows(file_url):
	"""The file's raw grid, header row included, blank rows dropped."""
	file_doc = frappe.get_doc("File", {"file_url": file_url})
	if cstr(file_doc.file_name).lower().endswith(".csv"):
		rows = read_csv_content(file_doc.get_content())
	else:
		rows = read_xlsx_file_from_attached_file(file_url=file_url)
	return [row for row in rows if any(cstr(cell).strip() for cell in row)]


def suggest_mapping(headers):
	"""Best-guess header -> field, so a file built from download_product_template() maps itself."""
	mapping = {}
	confidence = {}
	for header in headers:
		normalized = normalize_header(header)
		field, level = "", "none"
		for candidate, synonyms in FIELD_SYNONYMS.items():
			if normalized == synonyms[0]:
				field, level = candidate, "high"
				break
			if normalized in synonyms:
				field, level = candidate, "medium"
				break
		mapping[header] = field
		confidence[header] = level
	return mapping, confidence


def parse_and_validate(file_url: str, column_mapping: dict | None = None):
	"""One dry-run pass over the file: every row comes back with its own issue, or none. Nothing is
	written here — this is what both the Review step and run_import()'s own safety check share."""
	rows = read_uploaded_rows(file_url)
	if not rows:
		frappe.throw(_("The file has no rows"))

	headers = [cstr(cell) for cell in rows[0]]
	data_rows = rows[1:]

	suggested_mapping, confidence = suggest_mapping(headers)
	mapping = {header: column_mapping.get(header, "") for header in headers} if column_mapping else suggested_mapping

	missing_required = [FIELD_LABELS[field] for field in REQUIRED_FIELDS if field not in mapping.values()]
	if missing_required:
		frappe.throw(_("These columns are not mapped: {0}").format(", ".join(missing_required)))

	column_index_by_field = {}
	for index, header in enumerate(headers):
		field = mapping.get(header)
		if field:
			column_index_by_field.setdefault(field, index)

	def cell(row, field):
		index = column_index_by_field.get(field)
		return row[index] if index is not None and index < len(row) else None

	def as_amount(raw, label, issue_holder):
		# flt() swallows a bad string down to 0.0 instead of raising, which would silently turn
		# "not-a-number" into an unpriced row — parse strictly here so that surfaces as an error.
		if raw in (None, ""):
			return 0
		try:
			return flt(float(cstr(raw).replace(",", "").strip()))
		except (TypeError, ValueError):
			issue_holder.setdefault("issue", {"level": "error", "text": f'{label} "{raw}" is not a number'})
			return 0

	parsed_rows = []
	seen_variants = {}
	product_first_row = {}
	for offset, row in enumerate(data_rows):
		row_number = offset + 2  # +1 for the header row, +1 for 1-indexed row numbers
		title = cstr(cell(row, "title")).strip()
		collection = cstr(cell(row, "collection")).strip()
		color = cstr(cell(row, "color")).strip()
		size = cstr(cell(row, "size")).strip()

		holder = {}
		compare_at_price = as_amount(cell(row, "compare_at_price"), "Compare at price", holder)
		sale_price = as_amount(cell(row, "sale_price"), "Selling price", holder)
		stock = as_amount(cell(row, "stock"), "Stock", holder)
		issue = holder.get("issue")

		if not issue and not title:
			issue = {"level": "error", "text": "Product title is missing"}
		if not issue and not collection:
			issue = {"level": "error", "text": "Collection is missing"}
		elif not issue and not frappe.db.exists("Item Group", collection):
			issue = {"level": "error", "text": f'Collection "{collection}" does not exist — create it first'}
		if not issue and not color:
			issue = {"level": "error", "text": "Color is missing"}
		if not issue and not size:
			issue = {"level": "error", "text": "Size is missing"}

		if not issue and title:
			variant_key = (title.casefold(), color.casefold(), size.casefold())
			if variant_key in seen_variants:
				issue = {
					"level": "error",
					"text": f"Duplicate of row {seen_variants[variant_key]} (same title, colour and size)",
				}
			else:
				seen_variants[variant_key] = row_number

		if not issue and title:
			first = product_first_row.get(title.casefold())
			if first is None:
				product_first_row[title.casefold()] = {
					"row": row_number,
					"collection": collection,
					"compare_at_price": compare_at_price,
					"sale_price": sale_price,
				}
			elif collection and collection != first["collection"]:
				issue = {
					"level": "error",
					"text": f'Collection does not match row {first["row"]} for "{title}" ({first["collection"]})',
				}
			elif compare_at_price != first["compare_at_price"] or sale_price != first["sale_price"]:
				issue = {
					"level": "error",
					"text": (
						f'Price does not match row {first["row"]} for "{title}" — '
						"one price applies to the whole product"
					),
				}

		if not issue and not compare_at_price and not sale_price:
			issue = {"level": "warning", "text": "No price set — product is created without a price"}

		parsed_rows.append(
			{
				"row": row_number,
				"title": title,
				"collection": collection,
				"color": color,
				"size": size,
				"compare_at_price": compare_at_price,
				"sale_price": sale_price,
				"stock": stock,
				"issue": issue,
			}
		)

	groups = group_valid_rows(parsed_rows)
	counts = {
		"total": len(parsed_rows),
		"errors": sum(1 for row in parsed_rows if row["issue"] and row["issue"]["level"] == "error"),
		"warnings": sum(1 for row in parsed_rows if row["issue"] and row["issue"]["level"] == "warning"),
		"ready": sum(1 for row in parsed_rows if not row["issue"] or row["issue"]["level"] == "warning"),
		"products": len(groups),
	}

	return {
		"headers": headers,
		"mapping": mapping,
		"confidence": confidence,
		"rows": parsed_rows,
		"counts": counts,
	}


def group_valid_rows(parsed_rows):
	"""One entry per product title with zero error rows — only these are ever written. A title
	whose every row errors, or whose only clean rows are duplicates of an error, never groups."""
	groups = {}
	order = []
	for row in parsed_rows:
		if row["issue"] and row["issue"]["level"] == "error":
			continue
		key = row["title"].casefold()
		if key not in groups:
			groups[key] = {
				"title": row["title"],
				"collection": row["collection"],
				"compare_at_price": row["compare_at_price"],
				"sale_price": row["sale_price"],
				"rows": [],
			}
			order.append(key)
		groups[key]["rows"].append(row)
	return [groups[key] for key in order]


def group_to_option_sizes(rows):
	option_sizes = {}
	for row in rows:
		option_sizes.setdefault(row["color"], []).append(row["size"])
	return [{"option": option, "sizes": sizes} for option, sizes in option_sizes.items()]


def receive_group_stock(item_template, rows):
	"""Opening stock for a just-created product, one grouped read plus one receipt per colour —
	not one query per row regardless of how many size rows the file had for this product."""
	rows_with_stock = [row for row in rows if flt(row["stock"]) > 0]
	if not rows_with_stock:
		return

	configurator = frappe.db.get_value("Style Attribute Configurator", {"item_template": item_template})
	variants = frappe.get_all(
		"Style Attribute Variant", filters={"configurator": configurator}, fields=["name", "attribute_value"]
	)
	variant_by_option = {cstr(variant.attribute_value).casefold(): variant.name for variant in variants}

	size_items = frappe.get_all(
		"Color Size Item",
		filters={"parent": ["in", [variant.name for variant in variants]], "parenttype": "Style Attribute Variant"},
		fields=["parent", "size", "item_code"],
	)
	item_code_by_variant_size = {(row.parent, cstr(row.size).casefold()): row.item_code for row in size_items}

	quantities_by_variant = {}
	for row in rows_with_stock:
		variant_name = variant_by_option.get(row["color"].casefold())
		item_code = variant_name and item_code_by_variant_size.get((variant_name, row["size"].casefold()))
		if item_code:
			quantities_by_variant.setdefault(variant_name, {})[item_code] = flt(row["stock"])

	for variant_name, quantities in quantities_by_variant.items():
		frappe.get_doc("Style Attribute Variant", variant_name).receive_stock(quantities)


@frappe.whitelist()
def validate_import(file_url: str, column_mapping: dict | str | None = None):
	"""The Review step's data — a dry run, nothing written."""
	frappe.has_permission("Item", ptype="create", throw=True)
	if isinstance(column_mapping, str):
		column_mapping = frappe.parse_json(column_mapping)
	return parse_and_validate(file_url, column_mapping)


@frappe.whitelist(methods=["POST"])
def run_import(file_url: str, column_mapping: dict | str | None = None):
	"""Commits every product group that validated clean.

	Rows are validated in full before anything is written, so a bad row's product is never
	attempted at all. A group that still fails while being created (rare, since it already
	validated) is rolled back to its own savepoint, so one unlucky product never leaves orphaned
	Items behind and never blocks the rest of the file.
	"""
	frappe.has_permission("Item", ptype="create", throw=True)
	if isinstance(column_mapping, str):
		column_mapping = frappe.parse_json(column_mapping)

	if not frappe.db.exists("Item Attribute", OPTION_ATTRIBUTE):
		frappe.throw(_('This store has no Item Attribute named "{0}" — create it first.').format(OPTION_ATTRIBUTE))
	if not frappe.db.exists("Item Attribute", SIZE_ATTRIBUTE):
		frappe.throw(_('This store has no Item Attribute named "{0}" — create it first.').format(SIZE_ATTRIBUTE))

	result = parse_and_validate(file_url, column_mapping)
	groups = group_valid_rows(result["rows"])

	created = []
	creation_errors = []
	for group in groups:
		savepoint = frappe.generate_hash(length=10)
		try:
			frappe.db.savepoint(savepoint)
			created_product = create_product(
				title=group["title"],
				collection=group["collection"],
				option_attribute=OPTION_ATTRIBUTE,
				size_attribute=SIZE_ATTRIBUTE,
				option_sizes=group_to_option_sizes(group["rows"]),
				price=group["compare_at_price"] or None,
				sale_price=group["sale_price"] or None,
			)
			receive_group_stock(created_product["name"], group["rows"])
		except Exception as error:
			frappe.db.rollback(save_point=savepoint)
			message = str(error)
			for row in group["rows"]:
				creation_errors.append({"row": row["row"], "message": message})
		else:
			created.append({"item_template": created_product["name"], "title": group["title"]})

	# Rows that never made it into a group at all kept their own validation message from the dry run.
	validation_errors = [
		{"row": row["row"], "message": row["issue"]["text"]}
		for row in result["rows"]
		if row["issue"] and row["issue"]["level"] == "error"
	]

	return {
		"created": created,
		"created_count": len(created),
		"row_errors": validation_errors + creation_errors,
		"counts": result["counts"],
	}
