import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Cast_, Min
from frappe.utils import flt
from frappe.utils.caching import redis_cache

from ls_shop import seo
from ls_shop.search import query as search_query
from ls_shop.utils import (
	get_current_page,
	get_nested_links,
	get_product_base_query,
	get_product_list,
	get_total_product_count,
)

no_cache = 1


def get_filter_brands(filters=None):
	filter_copy = filters.copy() if filters else {}
	filter_copy.pop("brands", None)

	query = get_product_base_query(filter_copy)
	item = DocType("Item")

	query = query.select(item.brand).distinct().orderby(item.brand)
	# Values are returned raw: they round-trip through the checkbox value and the URL into a
	# case-sensitive SQLite IN on the index, and the template already display-cases them.
	return [brand for brand in query.run(pluck=True) if brand]


def get_filter_colors(filters=None):
	filter_copy = filters.copy() if filters else {}
	filter_copy.pop("colors", None)

	query = get_product_base_query(filter_copy)
	variant = DocType("Style Attribute Variant")

	query = query.select(variant.attribute_name).distinct().orderby(variant.attribute_name)
	return [color for color in query.run(pluck=True) if color]


def get_filter_sizes(filters=None):
	filter_copy = filters.copy() if filters else {}
	filter_copy.pop("sizes", None)

	query = get_product_base_query(filter_copy)
	color_size_item = DocType("Color Size Item")

	query = query.select(color_size_item.size).distinct().orderby(Cast_(color_size_item.size, "Decimal"))
	return query.run(pluck=True)


def get_category_tree(root_category):
	"""
	Recursively builds a tree of Item Groups from root_category using parent_item_group links.
	"""

	def build_node(category_name):
		doc = frappe.get_cached_doc("Item Group", category_name)

		# Get direct children of this node
		children = frappe.get_all(
			"Item Group",
			filters={
				"parent_item_group": category_name,
				"custom_display_on_website": True,
			},
			fields=["name", "is_group", "custom_item_group_display_name"],
			order_by="custom_item_group_display_name",
		)

		# Build child nodes recursively
		child_nodes = []
		for child in children:
			child_nodes.append(build_node(child.name))

		return {
			"name": doc.name,
			"display_name": doc.custom_item_group_display_name or doc.name,
			"children": child_nodes,
			"is_leaf": int(doc.is_group == 0),
		}

	return build_node(root_category)


def get_product_filters(selected_filters):
	"""Fetches available filters like brand, price range, and sizes."""
	# Define DocTypes
	category = selected_filters.get("category", "")
	item_price = DocType("Item Price")
	sale_price_list = frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "sale_price_list")
	# Get price range (min and max)
	price_range = (
		frappe.qb.from_(item_price)
		.select(
			Min(item_price.price_list_rate).as_("min_price"),
			frappe.query_builder.functions.Max(item_price.price_list_rate).as_("max_price"),
		)
		.where(item_price.price_list == sale_price_list)  # Adjust price list as needed
	).run(as_dict=True)

	# Get available sizes
	filters = {}

	# Get dynamic categories from Ecommerce Category doctype
	ecommerce_categories = frappe.get_all(
		"Ecommerce Category",
		filters={"enabled": 1},
		fields=["name", "category_name", "display_name", "item_group"],
		order_by="display_order asc, category_name asc",
	)

	if category:
		# If a specific category is selected, show its subcategories
		filters[category] = get_category_tree(category)["children"]
	else:
		# Show all enabled categories with their item group trees
		for ecom_cat in ecommerce_categories:
			# Use the linked item_group if available, otherwise use category_name
			item_group_name = ecom_cat.item_group or ecom_cat.category_name
			if frappe.db.exists("Item Group", item_group_name):
				try:
					filters[ecom_cat.display_name] = get_category_tree(item_group_name)["children"]
				except Exception:
					# If category tree fails, just skip this category
					pass

	# When SQLite serves the grid the sidebar must be faceted from the same result set, or a listed
	# brand/colour/size would filter down to nothing.
	facets = search_query.listing_facets(selected_filters)
	if facets:
		filters.update(facets)
	else:
		filters["brands"] = get_filter_brands(selected_filters)
		filters["sizes"] = get_filter_sizes(selected_filters)
		filters["colors"] = get_filter_colors(selected_filters)

	return filters, price_range[0] if price_range else {"min_price": 0, "max_price": 0}


def get_selected_filters():
	"""Extracts filters from URL query parameters."""
	query_params = frappe.form_dict

	filters = {
		"subcategory": query_params.get("subcategory", "").split(",")
		if query_params.get("subcategory")
		else [],
		"colors": query_params.get("colors", "").split(",") if query_params.get("colors") else [],
		"sizes": query_params.get("sizes", "").split(",") if query_params.get("sizes") else [],
		"brands": query_params.get("brands", "").split(",") if query_params.get("brands") else [],
		"search": query_params.get("search", ""),
		"category": query_params.get("category", ""),
		"has_discount": query_params.get("has_discount", "0") == "1",
	}
	min_price = query_params.get("min")
	max_price = query_params.get("max")

	# flt, not int: the price slider posts decimals (?min=74.5), which int() rejects with a 500.
	if min_price:
		filters["min_price"] = flt(min_price)
	if max_price:
		filters["max_price"] = flt(max_price)
	return filters


def get_sort_by(default_sort):
	return frappe.form_dict.get("sort_by") or default_sort


def get_context(context):
	page = get_current_page()
	selected_filters = get_selected_filters()
	# Fetch updated filters based on selected ones
	filters, price_range = get_product_filters(selected_filters)
	# Fetch filtered product list
	context.page_length = 30
	context.show_relevance_sort = search_query.relevance_sort_available(selected_filters)
	context.sort_by = get_sort_by("default" if context.show_relevance_sort else "new_arrival")
	products = get_product_list(
		filters=selected_filters,
		page=page,
		page_length=context.page_length,
		sort_by=context.sort_by,
	)
	# Pass data to frontend
	context.products = products
	context.current_page = page
	context.total_count = get_total_product_count(filters=selected_filters)  # Adjust for pagination
	context.filters = filters  # Updated filters
	context.selected_filters = selected_filters
	context.price_range = price_range  # Updated price range
	context.breadcrumbs = [
		{
			"label": "Products",
			"href": "#",
		}
	]
	context.category = selected_filters.get("category", "")

	category_doc = seo.get_category_seo_overrides(context.category)
	context.seo = seo.build_collection_seo(
		context.category,
		context.breadcrumbs,
		total_count=context.total_count,
		category_doc=category_doc,
	)
	context.json_ld = [
		seo.build_collection_json_ld(context.category, context.breadcrumbs, context.total_count),
		seo.build_breadcrumb_json_ld(context.breadcrumbs),
	]
