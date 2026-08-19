# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from erpnext.controllers.item_variant import create_variant
from frappe import _
from frappe.utils.data import cint, cstr, flt

from ls_shop.api.variant_pricing import get_selling_price_lists, set_variant_prices

PAGE_LENGTH = 20


@frappe.whitelist()
def get_products(search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH):
	"""One call, one complete Products screen.

	A store owner asking "what is the state of this product?" would otherwise open Item,
	Style Attribute Configurator, Item Price and each variant's publish flag in turn. Every
	lookup below is batched across the whole page so adding a column never costs a query
	per row.
	"""
	frappe.has_permission("Item", ptype="read", throw=True)

	start = cint(start)
	page_length = cint(page_length) or PAGE_LENGTH

	configurators = frappe.get_all(
		"Style Attribute Configurator",
		fields=["name", "item_template", "item_attribute"],
	)
	if not configurators:
		return {"products": [], "total": 0}

	templates_by_configurator = {row.name: row.item_template for row in configurators}

	item_filters = {"name": ["in", list(set(templates_by_configurator.values()))]}
	if search:
		item_filters["item_name"] = ["like", f"%{search}%"]

	total = frappe.db.count("Item", item_filters)
	templates = frappe.get_all(
		"Item",
		filters=item_filters,
		fields=["name", "item_name", "image", "item_group", "disabled"],
		order_by="modified desc",
		start=start,
		page_length=page_length,
	)
	if not templates:
		return {"products": [], "total": total}

	template_names = {row.name for row in templates}
	page_configurators = [
		name for name, template in templates_by_configurator.items() if template in template_names
	]

	variants = frappe.get_all(
		"Style Attribute Variant",
		filters={"configurator": ["in", page_configurators]},
		fields=["name", "configurator", "attribute_value", "display_name", "is_published", "route"],
	)
	variant_names = [row.name for row in variants]

	sizes = (
		frappe.get_all(
			"Color Size Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent", "size", "item_code"],
		)
		if variant_names
		else []
	)
	item_codes = [row.item_code for row in sizes if row.item_code]

	rates_by_item_code = get_default_rates(item_codes)
	stock_by_item_code = get_ecommerce_stock(item_codes)

	item_codes_by_variant = {}
	for row in sizes:
		if row.item_code:
			item_codes_by_variant.setdefault(row.parent, []).append(row.item_code)

	variants_by_template = {}
	for row in variants:
		template = templates_by_configurator.get(row.configurator)
		if template:
			variants_by_template.setdefault(template, []).append(row)

	products = []
	for template in templates:
		template_variants = variants_by_template.get(template.name, [])
		template_item_codes = [
			item_code for row in template_variants for item_code in item_codes_by_variant.get(row.name, [])
		]
		rates = [rates_by_item_code[code] for code in template_item_codes if code in rates_by_item_code]

		products.append(
			{
				"name": template.name,
				"title": template.item_name,
				"image": template.image,
				"collection": template.item_group,
				"disabled": bool(template.disabled),
				"variant_count": len(template_variants),
				"published_count": sum(1 for row in template_variants if row.is_published),
				"price_from": min(rates) if rates else None,
				"price_to": max(rates) if rates else None,
				"stock": sum(stock_by_item_code.get(code, 0) for code in template_item_codes),
				"variants": [
					{
						"name": row.name,
						"option": row.attribute_value or row.display_name,
						"is_published": bool(row.is_published),
						"route": row.route,
						"size_count": len(item_codes_by_variant.get(row.name, [])),
					}
					for row in template_variants
				],
			}
		)

	return {"products": products, "total": total}


def get_default_rates(item_codes):
	if not item_codes:
		return {}

	default_price_list, _sale_price_list = get_selling_price_lists()
	rows = frappe.get_all(
		"Item Price",
		filters={"item_code": ["in", item_codes], "price_list": default_price_list},
		fields=["item_code", "price_list_rate"],
	)
	return {cstr(row.item_code): flt(row.price_list_rate) for row in rows}


def get_ecommerce_stock(item_codes):
	if not item_codes:
		return {}

	warehouse = frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "ecommerce_warehouse")
	if not warehouse:
		# ponytail: stock reads as zero until the warehouse is set, revisit if multi-warehouse lands
		return {}

	rows = frappe.get_all(
		"Bin",
		filters={"item_code": ["in", item_codes], "warehouse": warehouse},
		fields=["item_code", "actual_qty"],
	)
	return {cstr(row.item_code): flt(row.actual_qty) for row in rows}


@frappe.whitelist()
def get_product(item_template: str):
	"""Everything one product's edit screen needs, in one call."""
	frappe.has_permission("Item", doc=item_template, ptype="read", throw=True)

	template = frappe.db.get_value(
		"Item",
		item_template,
		["name", "item_name", "image", "item_group", "disabled"],
		as_dict=True,
	)
	if not template:
		frappe.throw(_("Product {0} not found").format(item_template))

	configurators = frappe.get_all(
		"Style Attribute Configurator",
		filters={"item_template": item_template},
		fields=["name", "item_attribute"],
	)
	variants = (
		frappe.get_all(
			"Style Attribute Variant",
			filters={"configurator": ["in", [row.name for row in configurators]]},
			fields=["name", "attribute_value", "display_name", "is_published", "route"],
		)
		if configurators
		else []
	)
	variant_names = [row.name for row in variants]

	sizes = (
		frappe.get_all(
			"Color Size Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent", "size", "item_code"],
		)
		if variant_names
		else []
	)
	images = (
		frappe.get_all(
			"Website Slideshow Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent", "image"],
		)
		if variant_names
		else []
	)

	rates_by_item_code = get_default_rates([row.item_code for row in sizes if row.item_code])
	stock_by_item_code = get_ecommerce_stock([row.item_code for row in sizes if row.item_code])

	sizes_by_variant = {}
	for row in sizes:
		sizes_by_variant.setdefault(row.parent, []).append(
			{
				"size": row.size,
				"item_code": row.item_code,
				"rate": rates_by_item_code.get(cstr(row.item_code)),
				"stock": stock_by_item_code.get(cstr(row.item_code), 0),
			}
		)

	images_by_variant = {}
	for row in images:
		images_by_variant.setdefault(row.parent, []).append(row.image)

	return {
		"name": template.name,
		"title": template.item_name,
		"image": template.image,
		"collection": template.item_group,
		"disabled": bool(template.disabled),
		"option_attribute": configurators[0].item_attribute if configurators else None,
		"variants": [
			{
				"name": row.name,
				"option": row.attribute_value or row.display_name,
				"is_published": bool(row.is_published),
				"route": row.route,
				"sizes": sizes_by_variant.get(row.name, []),
				"images": images_by_variant.get(row.name, []),
				# The storefront refuses to publish without both, so say so before the owner
				# clicks Publish rather than as an error afterwards.
				"blockers": get_publish_blockers(
					images_by_variant.get(row.name, []), sizes_by_variant.get(row.name, [])
				),
			}
			for row in variants
		],
	}


def get_publish_blockers(images, sizes):
	blockers = []
	if not images:
		blockers.append(_("Add at least one image"))
	if not sizes:
		blockers.append(_("Add at least one size"))
	return blockers


@frappe.whitelist()
def get_collections():
	"""The collections a product can be filed under, for the create form's picker."""
	frappe.has_permission("Item Group", ptype="read", throw=True)
	return frappe.get_all("Item Group", fields=["name"], order_by="name", pluck="name")


@frappe.whitelist(methods=["POST"])
def create_product(
	title: str,
	collection: str,
	option_attribute: str,
	options: list | str,
	size_attribute: str,
	sizes: list | str,
	price=None,
	sale_price=None,
):
	"""Create a sellable product from what a store owner actually knows.

	Company, warehouse, price list, UOM and naming series come from Lifestyle Settings and are
	never asked for - a shop owner coming from Shopify has no reason to know them.
	"""
	frappe.has_permission("Item", ptype="create", throw=True)

	title = cstr(title).strip()
	if not title:
		frappe.throw(_("Enter a product title"))

	options = [cstr(value).strip() for value in frappe.parse_json(options) if cstr(value).strip()]
	sizes = [cstr(value).strip() for value in frappe.parse_json(sizes) if cstr(value).strip()]
	if not options:
		frappe.throw(_("Add at least one option, for example a colour"))
	if not sizes:
		frappe.throw(_("Add at least one size"))

	if not frappe.db.exists("Item Group", collection):
		frappe.throw(_("Collection {0} does not exist. Create it first.").format(collection))

	options = add_missing_attribute_values(option_attribute, options)
	sizes = add_missing_attribute_values(size_attribute, sizes)

	item_template = frappe.new_doc("Item")
	item_template.item_code = title
	item_template.item_name = title
	item_template.item_group = collection
	item_template.stock_uom = get_default_stock_uom()
	item_template.is_stock_item = 1
	item_template.has_variants = 1
	item_template.variant_based_on = "Item Attribute"
	item_template.append("attributes", {"attribute": option_attribute})
	item_template.append("attributes", {"attribute": size_attribute})
	item_template.insert()

	for option in options:
		for size in sizes:
			size_item = create_variant(item_template.name, {option_attribute: option, size_attribute: size})
			size_item.insert()

	configurator = frappe.new_doc("Style Attribute Configurator")
	configurator.item_template = item_template.name
	configurator.item_attribute = option_attribute
	configurator.insert()
	# after_insert only generates variants when the setting says so; a product created here is
	# useless without them, so make sure they exist either way.
	if not frappe.db.exists("Style Attribute Variant", {"configurator": configurator.name}):
		configurator.generate_variants()

	if flt(price) > 0 or flt(sale_price) > 0:
		set_variant_prices(item_template.name, default_rate=price, sale_rate=sale_price)

	return {"name": item_template.name}


def add_missing_attribute_values(attribute: str, values: list):
	"""Let the owner type a new colour without visiting the Item Attribute form.

	Returns the values in the attribute's own spelling. ERPNext compares attribute values
	case-insensitively, so treating "red" as new when "Red" exists appends a duplicate and the
	save is rejected - the owner typed a colour that already exists and got a validation error.
	"""
	attribute_doc = frappe.get_doc("Item Attribute", attribute)
	canonical_by_key = {
		cstr(row.attribute_value).casefold(): cstr(row.attribute_value)
		for row in attribute_doc.item_attribute_values
	}

	resolved = []
	taken = {cstr(row.abbr).casefold() for row in attribute_doc.item_attribute_values}
	added = False
	for value in values:
		canonical = canonical_by_key.get(cstr(value).casefold())
		if canonical:
			resolved.append(canonical)
			continue

		abbreviation = make_unique_abbreviation(value, taken)
		taken.add(abbreviation.casefold())
		canonical_by_key[cstr(value).casefold()] = value
		attribute_doc.append("item_attribute_values", {"attribute_value": value, "abbr": abbreviation})
		resolved.append(value)
		added = True

	if added:
		attribute_doc.save()

	return resolved


def make_unique_abbreviation(value: str, taken: set):
	base = "".join(part[0] for part in cstr(value).split() if part).upper() or "X"
	if base.casefold() not in taken:
		return base

	suffix = 2
	while f"{base}{suffix}".casefold() in taken:
		suffix += 1
	return f"{base}{suffix}"


def get_default_stock_uom():
	return frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos"


@frappe.whitelist(methods=["POST"])
def update_product(item_template: str, title=None, collection=None, disabled=None):
	frappe.has_permission("Item", doc=item_template, ptype="write", throw=True)

	item = frappe.get_doc("Item", item_template)
	if title is not None:
		item.item_name = cstr(title).strip()
	if collection is not None:
		item.item_group = collection
	if disabled is not None:
		item.disabled = cint(disabled)
	item.save()

	return {"name": item.name}


@frappe.whitelist(methods=["POST"])
def set_variant_published(style_attribute_variant: str, publish):
	"""Publish or unpublish one option.

	The variant controller refuses to publish without images and sizes; surface that as a
	message the owner can act on instead of a bare validation failure.
	"""
	variant = frappe.get_doc("Style Attribute Variant", style_attribute_variant)
	variant.check_permission("write")

	publish = cint(publish)
	if publish:
		blockers = get_publish_blockers(variant.images, variant.sizes)
		if blockers:
			frappe.throw(_("Cannot publish yet: {0}").format(", ".join(blockers)))

	variant.is_published = publish
	variant.save()

	return {"name": variant.name, "is_published": bool(variant.is_published)}


@frappe.whitelist(methods=["POST"])
def add_product_images(style_attribute_variant: str, file_urls: list | str):
	"""Attach already-uploaded files to an option, then report what still blocks publishing.

	The dashboard's whole point is that the owner never has to guess why a product is not live,
	so every write that can change publishability hands the blockers straight back.
	"""
	variant = frappe.get_doc("Style Attribute Variant", style_attribute_variant)
	variant.add_images(file_urls)
	variant.reload()

	return {
		"name": variant.name,
		"images": [row.image for row in variant.images],
		"blockers": get_publish_blockers(variant.images, variant.sizes),
	}


@frappe.whitelist(methods=["POST"])
def remove_product_image(style_attribute_variant: str, file_url: str):
	variant = frappe.get_doc("Style Attribute Variant", style_attribute_variant)
	variant.remove_image(file_url)
	variant.reload()

	return {
		"name": variant.name,
		"images": [row.image for row in variant.images],
		"blockers": get_publish_blockers(variant.images, variant.sizes),
	}


@frappe.whitelist(methods=["POST"])
def save_product_prices(style_attribute_variant: str, size_prices: list | str):
	"""Edit the per-size default and sale prices of one option."""
	variant = frappe.get_doc("Style Attribute Variant", style_attribute_variant)
	return variant.save_size_prices(size_prices)


@frappe.whitelist(methods=["POST"])
def receive_product_stock(
	style_attribute_variant: str, received_quantities: dict | str, valuation_rates: dict | str | None = None
):
	"""Take stock in against one option - a submitted Material Receipt into the shop warehouse."""
	variant = frappe.get_doc("Style Attribute Variant", style_attribute_variant)
	return {"stock_entry": variant.receive_stock(received_quantities, valuation_rates)}


@frappe.whitelist(methods=["POST"])
def set_product_published(item_template: str, publish):
	"""Publish or unpublish every option of a product in one go.

	Options that are not ready are skipped rather than failing the whole request, and come back
	named so the owner can see which ones still need work.
	"""
	frappe.has_permission("Item", doc=item_template, ptype="write", throw=True)

	publish = cint(publish)
	configurators = frappe.get_all(
		"Style Attribute Configurator", filters={"item_template": item_template}, pluck="name"
	)
	if not configurators:
		return {"updated": [], "skipped": []}

	variants = frappe.get_all(
		"Style Attribute Variant",
		filters={"configurator": ["in", configurators]},
		fields=["name", "attribute_value", "display_name"],
	)
	variant_names = [row.name for row in variants]

	# Work out readiness for the whole set in two queries; loading each variant just to count
	# its images and sizes would be a read per row.
	ready = get_ready_variant_names(variant_names) if publish else set(variant_names)

	updated = []
	skipped = []
	for row in variants:
		label = row.attribute_value or row.display_name
		if row.name not in ready:
			skipped.append(label)
			continue

		# ponytail: one save per option so validation and route generation still run,
		# move to a background job if a product ever carries more than a few dozen options
		variant = frappe.get_doc("Style Attribute Variant", row.name)
		variant.is_published = publish
		variant.save()
		updated.append(label)

	return {"updated": updated, "skipped": skipped}


def get_ready_variant_names(variant_names):
	"""The variants that carry both an image and a size, so they are allowed to go live."""
	if not variant_names:
		return set()

	with_images = {
		row.parent
		for row in frappe.get_all(
			"Website Slideshow Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent"],
		)
	}
	with_sizes = {
		row.parent
		for row in frappe.get_all(
			"Color Size Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent"],
		)
	}
	return with_images & with_sizes
