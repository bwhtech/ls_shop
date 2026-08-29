# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from erpnext.controllers.item_variant import create_variant
from frappe import _
from frappe.utils import get_url
from frappe.utils.data import cint, cstr, flt

from ls_shop.api.variant_pricing import get_selling_price_lists, set_variant_prices

PAGE_LENGTH = 20


@frappe.whitelist()
def get_products(search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH):
	"""One call, one complete Products screen.

	Every lookup is batched across the page, so adding a column never costs a query per row.
	"""
	frappe.has_permission("Item", ptype="read", throw=True)

	# Imported here because orders imports this module at import time; a module-level import would cycle.
	from ls_shop.api.admin.orders import get_reporting_currency

	currency = get_reporting_currency()

	start = cint(start)
	page_length = cint(page_length) or PAGE_LENGTH

	configurators = frappe.get_all(
		"Style Attribute Configurator",
		fields=["name", "item_template", "item_attribute"],
	)
	if not configurators:
		return {"products": [], "total": 0, "currency": currency}

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
		return {"products": [], "total": total, "currency": currency}

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

	# A dashboard-created product never sets Item.image, so fall back to the first option image.
	first_image_by_variant = {}
	if variant_names:
		for row in frappe.get_all(
			"Website Slideshow Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent", "image"],
			order_by="idx asc",
		):
			first_image_by_variant.setdefault(row.parent, row.image)

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
				"image": template.image
				or next(
					(
						first_image_by_variant[row.name]
						for row in template_variants
						if row.name in first_image_by_variant
					),
					None,
				),
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

	return {"products": products, "total": total, "currency": currency}


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
		["name", "item_name", "image", "item_group", "description", "disabled"],
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
		"description": template.description,
		"disabled": bool(template.disabled),
		"option_attribute": configurators[0].item_attribute if configurators else None,
		"variants": [
			{
				"name": row.name,
				"option": row.attribute_value or row.display_name,
				"is_published": bool(row.is_published),
				"route": row.route,
				"storefront_url": get_url(f"/products/{row.route}") if row.route else None,
				"sizes": sizes_by_variant.get(row.name, []),
				"images": images_by_variant.get(row.name, []),
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
def get_collections(search_text: str | None = None):
	"""The collections a product can be filed under, for the create form's picker."""
	frappe.has_permission("Item Group", ptype="read", throw=True)

	filters = {}
	if search_text:
		filters["name"] = ("like", f"%{cstr(search_text)}%")

	# ponytail: first 100 matches only, paginate the picker if a store keeps more collections
	# than a searched dropdown can show
	return frappe.get_all("Item Group", filters=filters, order_by="name", pluck="name", limit=100)


@frappe.whitelist()
def get_attribute_values(attribute: str):
	"""The colours and sizes this store already uses, so the create form suggests instead of retypes."""
	frappe.has_permission("Item Attribute", doc=attribute, ptype="read", throw=True)

	return frappe.get_all(
		"Item Attribute Value",
		filters={"parent": attribute, "parenttype": "Item Attribute"},
		order_by="idx asc",
		pluck="attribute_value",
	)


@frappe.whitelist(methods=["POST"])
def create_product(
	title: str,
	collection: str,
	option_attribute: str,
	size_attribute: str,
	option_sizes: list | str,
	price=None,
	sale_price=None,
):
	"""Create a sellable product. Company, warehouse, price list, UOM and naming series
	come from Lifestyle Settings."""
	frappe.has_permission("Item", ptype="create", throw=True)

	title = cstr(title).strip()
	if not title:
		frappe.throw(_("Enter a product title"))

	option_sizes = parse_option_sizes(option_sizes)

	if not frappe.db.exists("Item Group", collection):
		frappe.throw(_("Collection {0} does not exist. Create it first.").format(collection))

	option_sizes = resolve_option_sizes(option_attribute, size_attribute, option_sizes)

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

	for option, sizes in option_sizes:
		for size in sizes:
			size_item = create_variant(item_template.name, {option_attribute: option, size_attribute: size})
			size_item.insert()

	configurator = frappe.new_doc("Style Attribute Configurator")
	configurator.item_template = item_template.name
	configurator.item_attribute = option_attribute
	configurator.insert()
	# after_insert only generates variants when the setting says so, and a product here needs them.
	if not frappe.db.exists("Style Attribute Variant", {"configurator": configurator.name}):
		configurator.generate_variants()

	if flt(price) > 0 or flt(sale_price) > 0:
		set_variant_prices(item_template.name, default_rate=price, sale_rate=sale_price)

	return {"name": item_template.name}


def parse_option_sizes(option_sizes: list | str):
	"""ERPNext compares attribute values case-insensitively, so two spellings of one colour
	are merged here or the second create_variant collides."""
	rows = frappe.parse_json(option_sizes) or []
	if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
		frappe.throw(_("Colours and sizes could not be read"))

	merged = {}
	for row in rows:
		option = cstr(row.get("option")).strip()
		if not option:
			continue

		sizes = merged.setdefault(option.casefold(), (option, []))[1]
		taken = {size.casefold() for size in sizes}
		for value in row.get("sizes") or []:
			size = cstr(value).strip()
			if size and size.casefold() not in taken:
				sizes.append(size)
				taken.add(size.casefold())

	if not merged:
		frappe.throw(_("Add at least one option, for example a colour"))

	for option, sizes in merged.values():
		if not sizes:
			frappe.throw(_("Pick at least one size for {0}").format(option))

	return list(merged.values())


def resolve_option_sizes(option_attribute: str, size_attribute: str, option_sizes: list):
	"""Swap what the owner typed for the spelling the Item Attribute already holds."""
	typed_options = [option for option, _sizes in option_sizes]
	typed_sizes = []
	taken = set()
	for _option, sizes in option_sizes:
		for size in sizes:
			if size.casefold() not in taken:
				typed_sizes.append(size)
				taken.add(size.casefold())

	canonical_options = add_missing_attribute_values(option_attribute, typed_options)
	canonical_sizes = add_missing_attribute_values(size_attribute, typed_sizes)
	size_by_typed = dict(zip(typed_sizes, canonical_sizes, strict=True))

	return [
		(canonical_options[index], [size_by_typed[size] for size in sizes])
		for index, (_option, sizes) in enumerate(option_sizes)
	]


def add_missing_attribute_values(attribute: str, values: list):
	"""Let the owner type a new colour without visiting the Item Attribute form.

	ERPNext compares attribute values case-insensitively, so "red" beside "Red" appends a duplicate.
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
def update_product(item_template: str, title=None, collection=None, description=None, disabled=None):
	frappe.has_permission("Item", doc=item_template, ptype="write", throw=True)

	item = frappe.get_doc("Item", item_template)
	if title is not None:
		# Item.validate backfills a blank item_name from item_code, so a cleared title silently survives.
		title = cstr(title).strip()
		if not title:
			frappe.throw(_("Title is required."))
		item.item_name = title
	if collection is not None:
		if not frappe.db.exists("Item Group", collection):
			frappe.throw(_("Collection {0} does not exist.").format(collection))
		item.item_group = collection
	if description is not None:
		item.description = description
	if disabled is not None:
		item.disabled = cint(disabled)
	item.save()

	return {"name": item.name}


@frappe.whitelist(methods=["POST"])
def set_variant_published(style_attribute_variant: str, publish):
	"""Publish or unpublish one option.

	The variant controller refuses to publish without images and sizes.
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
	"""Attach already-uploaded files to an option, then report what still blocks publishing."""
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

	Options that are not ready are skipped rather than failing the whole request, and come back named.
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

	# Two queries for the whole set; loading each variant to count images and sizes is a read per row.
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


def get_unpublishable_options(limit: int = 5):
	"""Options that cannot go live yet, with the reason, across the whole catalogue."""
	variants = frappe.get_all(
		"Style Attribute Variant",
		filters={"is_published": 0},
		fields=["name", "configurator", "attribute_value", "display_name"],
		order_by="modified desc",
	)
	if not variants:
		return []

	variant_names = [row.name for row in variants]
	sized_variants = {
		row.parent
		for row in frappe.get_all(
			"Color Size Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent"],
		)
	}
	imaged_variants = {
		row.parent
		for row in frappe.get_all(
			"Website Slideshow Item",
			filters={"parent": ["in", variant_names], "parenttype": "Style Attribute Variant"},
			fields=["parent"],
		)
	}

	templates_by_configurator = {
		row.name: row.item_template
		for row in frappe.get_all(
			"Style Attribute Configurator",
			filters={"name": ["in", list({row.configurator for row in variants if row.configurator})]},
			fields=["name", "item_template"],
		)
	}
	titles = {
		row.name: row.item_name
		for row in frappe.get_all(
			"Item",
			filters={"name": ["in", list(set(templates_by_configurator.values()))]},
			fields=["name", "item_name"],
		)
	}

	blocked = []
	for row in variants:
		# The blocker rule reads presence, not content, so membership sets stand in for the lists.
		blockers = get_publish_blockers(
			[1] if row.name in imaged_variants else [], [1] if row.name in sized_variants else []
		)
		if not blockers:
			continue

		template = templates_by_configurator.get(row.configurator)
		if not template:
			# An option whose configurator or template is gone has no product screen to link to.
			continue

		blocked.append(
			{
				"variant": row.name,
				"product": template,
				"title": titles.get(template) or template,
				"option": row.attribute_value or row.display_name,
				"blockers": blockers,
			}
		)
		if len(blocked) >= cint(limit):
			break

	return blocked
