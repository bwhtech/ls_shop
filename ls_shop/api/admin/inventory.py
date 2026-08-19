# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import cint, cstr, flt

PAGE_LENGTH = 50
LOW_STOCK_THRESHOLD = 5


@frappe.whitelist()
def get_inventory(
	availability: str | None = None, search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH
):
	"""Every sellable size and what is left of it.

	The question this screen answers is "what am I about to run out of", which no per-product
	page can answer - so it reads across every variant at once, in a fixed number of queries.
	"""
	frappe.has_permission("Item", ptype="read", throw=True)

	variants = frappe.get_all(
		"Style Attribute Variant",
		fields=["name", "attribute_value", "display_name", "item_style", "is_published"],
	)
	if not variants:
		return {"rows": [], "total": 0, "low_stock_threshold": LOW_STOCK_THRESHOLD}

	variant_by_name = {row.name: row for row in variants}
	sizes = frappe.get_all(
		"Color Size Item",
		filters={"parent": ["in", list(variant_by_name)], "parenttype": "Style Attribute Variant"},
		fields=["parent", "size", "item_code"],
	)
	item_codes = [row.item_code for row in sizes if row.item_code]
	if not item_codes:
		return {"rows": [], "total": 0, "low_stock_threshold": LOW_STOCK_THRESHOLD}

	titles = {
		row.name: row.item_name
		for row in frappe.get_all(
			"Item",
			filters={"name": ["in", list({row.item_style for row in variants if row.item_style})]},
			fields=["name", "item_name"],
		)
	}
	stock_by_item_code = get_stock_levels(item_codes)

	rows = []
	for size in sizes:
		if not size.item_code:
			continue

		variant = variant_by_name.get(size.parent)
		if not variant:
			continue

		quantity = stock_by_item_code.get(cstr(size.item_code), 0)
		rows.append(
			{
				"item_code": size.item_code,
				"product": titles.get(variant.item_style) or variant.item_style,
				"product_name": variant.item_style,
				"option": variant.attribute_value or variant.display_name,
				"variant": variant.name,
				"size": size.size,
				"stock": quantity,
				"is_published": bool(variant.is_published),
				"availability": describe_availability(quantity),
			}
		)

	if availability in ("out", "low"):
		rows = [
			row for row in rows if row["availability"] == ("Out of stock" if availability == "out" else "Low")
		]
	if search:
		needle = cstr(search).casefold()
		rows = [
			row
			for row in rows
			if needle in cstr(row["product"]).casefold() or needle in cstr(row["item_code"]).casefold()
		]

	# Whatever is closest to running out is what the owner needs to see first.
	rows.sort(key=lambda row: (row["stock"], cstr(row["product"])))

	start = cint(start)
	page_length = cint(page_length) or PAGE_LENGTH
	return {
		"rows": rows[start : start + page_length],
		"total": len(rows),
		"low_stock_threshold": LOW_STOCK_THRESHOLD,
	}


def describe_availability(quantity):
	if quantity <= 0:
		return "Out of stock"
	if quantity <= LOW_STOCK_THRESHOLD:
		return "Low"
	return "In stock"


def get_stock_levels(item_codes):
	warehouse = frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "ecommerce_warehouse")
	if not warehouse:
		# ponytail: stock reads as zero until the shop warehouse is set, revisit for multi-warehouse
		return {}

	rows = frappe.get_all(
		"Bin",
		filters={"item_code": ["in", item_codes], "warehouse": warehouse},
		fields=["item_code", "actual_qty"],
	)
	return {cstr(row.item_code): flt(row.actual_qty) for row in rows}


@frappe.whitelist(methods=["POST"])
def receive_stock(received_quantities: dict | str):
	"""Take stock in across any mix of products in one receipt.

	Grouped by variant because that is the level the existing receive_stock guards operate at -
	it validates that an item really is a size of the variant before moving anything.
	"""
	received_quantities = frappe.parse_json(received_quantities)
	if not isinstance(received_quantities, dict):
		frappe.throw(_("received_quantities must map item codes to quantities"))

	wanted = {
		cstr(code): flt(quantity) for code, quantity in received_quantities.items() if flt(quantity) > 0
	}
	if not wanted:
		frappe.throw(_("Enter a quantity for at least one item"))

	rows = frappe.get_all(
		"Color Size Item",
		filters={"item_code": ["in", list(wanted)], "parenttype": "Style Attribute Variant"},
		fields=["item_code", "parent"],
	)
	quantities_by_variant = {}
	for row in rows:
		quantities_by_variant.setdefault(row.parent, {})[cstr(row.item_code)] = wanted[cstr(row.item_code)]

	unknown = sorted(set(wanted) - {cstr(row.item_code) for row in rows})
	if unknown:
		frappe.throw(_("Not a sellable size: {0}").format(", ".join(unknown)))

	stock_entries = []
	for variant_name, quantities in quantities_by_variant.items():
		variant = frappe.get_doc("Style Attribute Variant", variant_name)
		stock_entries.append(variant.receive_stock(quantities))

	return {"stock_entries": stock_entries}
