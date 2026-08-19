# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

from urllib.parse import quote

import frappe
from frappe.query_builder.functions import Max
from frappe.utils import cint
from frappe.utils.nestedset import NestedSet, update_move_node

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.editor_input import require_safe_url

# root tab -> mega-menu column -> link. Deeper levels exist in no storefront theme.
MAX_MENU_DEPTH = 3


def root_filter():
	"""Filter value matching top-level entries, for use with ``frappe.get_all``.

	``create_node`` writes ``parent or None``, so roots hold NULL, while NestedSet's own writes and
	rows that predate it hold "". Only DatabaseQuery (``frappe.get_all``) wraps the column in
	``ifnull`` — ``frappe.db.get_value`` emits a plain comparison and silently matches neither.
	"""
	return ["in", ["", None]]


class EcommerceCategory(NestedSet):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		category_name: DF.Data
		display_name: DF.Data
		display_order: DF.Int
		enabled: DF.Check
		icon: DF.Data | None
		image: DF.AttachImage | None
		is_group: DF.Check
		item_group: DF.Link | None
		lft: DF.Int
		link_brand: DF.Link | None
		link_type: DF.Literal["", "Item Group", "Brand", "URL"]
		link_url: DF.Data | None
		meta_description: DF.SmallText | None
		meta_title: DF.Data | None
		noindex: DF.Check
		og_image: DF.AttachImage | None
		old_parent: DF.Link | None
		parent_ecommerce_category: DF.Link | None
		rgt: DF.Int
		route_slug: DF.Data | None

	# end: auto-generated types

	nsm_parent_field = "parent_ecommerce_category"

	def on_update(self):
		# Bulk tree copies place every row first and rebuild the bounds once, instead of paying two
		# full-table updates per row. The flag is private to this doctype on purpose: ERPNext's own
		# Account and Department controllers read frappe.local.flags.ignore_update_nsm, so holding
		# that one across an insert would skip their bookkeeping and corrupt the chart of accounts.
		if self.flags.ignore_update_nsm or frappe.local.flags.ignore_ecommerce_category_nsm:
			# update_nsm decides what a later save or delete owes the tree by comparing old_parent
			# against the parent field, so the skipped bookkeeping still has to happen. Left NULL,
			# both sides read as "no parent" and nothing runs: deleting the row never reclaims its
			# lft/rgt band, and dragging it out to the top level leaves the band inside its old
			# parent, so get_descendants_of keeps returning it.
			self.db_set("old_parent", self.parent_ecommerce_category or "", update_modified=False)
			return
		super().on_update()

	def on_trash(self, allow_root_deletion=False):
		# A root holds old_parent "" and on_trash blanks the parent field to "" as well, so update_nsm
		# compares "" against "", takes neither the add nor the move branch, and the row is deleted
		# with its lft/rgt band still reserved — a permanent hole. Re-seating the root at the end of
		# the tree first moves that band to where the delete lands.
		if not self.get(self.nsm_parent_field) and cint(self.rgt) < self.last_bound():
			self.validate_if_child_exists()
			update_move_node(self, self.nsm_parent_field)
		super().on_trash(allow_root_deletion)

	def last_bound(self):
		category = frappe.qb.DocType(self.doctype)
		return cint(frappe.qb.from_(category).select(Max(category.rgt)).run(pluck=True)[0])

	def validate(self):
		self.validate_route_slug()
		self.validate_link_target()
		self.validate_depth()
		self.set_defaults()

	def validate_link_target(self):
		"""Keep only the target the selected link type uses, and check it.

		Switching a type in the Desk form leaves the old target on the doc; left there, a later
		switch back silently resurrects a target the shop owner thought they had cleared.

		A menu URL is written straight into an href on a public page, and Frappe's Jinja environment
		has autoescaping off, so a `javascript:` scheme here is stored XSS. The navbar editor
		endpoint already checks this, but a Desk form write, a REST insert or a fixture bypasses that
		endpoint — the model is the only place that covers every write path.
		"""
		if self.link_type != "Item Group":
			self.item_group = None
		if self.link_type != "Brand":
			self.link_brand = None
		if self.link_type != "URL":
			self.link_url = None
			return

		self.link_url = require_safe_url(self.link_url, frappe._("URL is required."))

	def validate_route_slug(self):
		"""Only top-level entries own a storefront URL, so only they need a slug.

		A nested entry is reached through its parent's listing page; forcing a slug on it would
		burn a unique route on something no shopper can land on.
		"""
		if self.parent_ecommerce_category:
			self.route_slug = None
			return

		self.route_slug = frappe.scrub(self.route_slug or self.category_name)

		duplicate = frappe.get_all(
			"Ecommerce Category",
			filters={
				"route_slug": self.route_slug,
				"name": ["!=", self.name],
				"parent_ecommerce_category": root_filter(),
			},
			limit=1,
			pluck="name",
		)
		if duplicate:
			frappe.throw(
				frappe._("Route slug '{0}' is already used by {1}").format(self.route_slug, duplicate[0])
			)

	def validate_depth(self):
		depth = get_depth(self.parent_ecommerce_category) + 1
		height = get_subtree_height(self.name) if not self.is_new() else 0
		if depth + height > MAX_MENU_DEPTH:
			frappe.throw(
				frappe._("Menus are limited to {0} levels — this move would push '{1}' past that.").format(
					MAX_MENU_DEPTH, self.display_name or self.category_name
				)
			)

	def set_defaults(self):
		if not self.display_name:
			self.display_name = self.category_name


def build_listing_href(root_slug, item_group, language):
	"""Product listing URL for one item group, as the `?subcategory=` filter expects."""
	subcategory = quote(item_group)
	if root_slug:
		return f"/{language}/products?category={root_slug}&subcategory={subcategory}"
	return f"/{language}/products?subcategory={subcategory}"


def get_depth(name):
	"""Level this entry sits on, counting from 1 — a top-level tab is 1, and an empty name is 0.

	Callers placing a new child pass its parent and add 1.
	"""
	depth = 0
	while name and depth <= MAX_MENU_DEPTH:
		name = frappe.db.get_value("Ecommerce Category", name, "parent_ecommerce_category")
		depth += 1
	return depth


def get_subtree_height(name):
	"""Levels hanging below this entry — 0 for a leaf, 1 when it has children only."""
	height = 0
	names = [name]
	while names and height <= MAX_MENU_DEPTH:
		names = frappe.get_all(
			"Ecommerce Category", filters={"parent_ecommerce_category": ["in", names]}, pluck="name"
		)
		if names:
			height += 1
	return height


def get_menu_tree(enabled_only=False):
	"""The whole menu as nested nodes, in one query.

	Read on every storefront render, so it never walks the tree per node: one ordered pass over the
	entries, assembled in Python.
	"""
	filters = {"enabled": 1} if enabled_only else {}
	entries = frappe.get_all(
		"Ecommerce Category",
		filters=filters,
		fields=[
			"name",
			"category_name",
			"display_name",
			"parent_ecommerce_category",
			"enabled",
			"display_order",
			"route_slug",
			"link_type",
			"item_group",
			"link_brand",
			"link_url",
			"icon",
			"image",
			"meta_title",
			"meta_description",
			"og_image",
			"noindex",
			"lft",
		],
		order_by="lft asc",
	)
	if not entries:
		return []

	language = frappe.local.lang or "en"
	nodes = {}
	roots = []
	for entry in entries:
		nodes[entry.name] = {
			"name": entry.name,
			"label": entry.display_name or entry.category_name,
			"parent": entry.parent_ecommerce_category or "",
			"route_slug": entry.route_slug or "",
			"link_type": entry.link_type or "",
			"item_group": entry.item_group or "",
			"brand": entry.link_brand or "",
			"url": entry.link_url or "",
			"icon": entry.icon or "",
			"image": entry.image or "",
			"meta_title": entry.meta_title or "",
			"meta_description": entry.meta_description or "",
			"og_image": entry.og_image or "",
			# A checkbox, not a string: `or ""` would turn an unticked 0 into a blank the editor
			# cannot tell from "never set", leaving the control indeterminate.
			"noindex": cint(entry.noindex),
			"visible": bool(entry.enabled),
			"display_order": entry.display_order,
			"children": [],
		}

	for entry in entries:
		node = nodes[entry.name]
		if not entry.parent_ecommerce_category:
			roots.append(node)
			continue
		parent = nodes.get(entry.parent_ecommerce_category)
		# A hidden entry takes its whole branch with it rather than promoting the children to tabs.
		if parent:
			parent["children"].append(node)

	for node in nodes.values():
		node["children"].sort(key=lambda child: (child["display_order"] or 0, child["label"]))
	roots.sort(key=lambda node: (node["display_order"] or 0, node["label"]))

	for root in roots:
		set_hrefs(root, root["route_slug"] or root["name"], language)

	return roots


def set_hrefs(node, root_slug, language):
	node["href"] = get_node_href(node, root_slug, language)
	for child in node["children"]:
		set_hrefs(child, root_slug, language)


def get_node_href(node, root_slug, language):
	if node["link_type"] == "URL":
		return node["url"] or None
	if node["link_type"] == "Brand":
		return f"/{language}/products?brands={quote(node['brand'])}" if node["brand"] else None
	if node["link_type"] == "Item Group" and node["item_group"]:
		return build_listing_href(root_slug, node["item_group"], language)
	if not node["parent"]:
		return f"/{language}/products?category={root_slug}"
	return None


@frappe.whitelist()
def get_active_categories():
	"""Get all active categories ordered by display_order"""
	return frappe.get_all(
		"Ecommerce Category",
		filters={"enabled": 1},
		fields=[
			"name",
			"category_name",
			"display_name",
			"route_slug",
			"icon",
			"image",
			"display_order",
		],
		order_by="display_order asc, category_name asc",
	)


@frappe.whitelist()
def get_category_by_slug(slug: str):
	"""Get category details by route slug"""
	return frappe.get_all(
		"Ecommerce Category",
		filters={"route_slug": slug, "enabled": 1},
		fields=["name", "category_name", "display_name", "route_slug", "icon", "image"],
		limit=1,
	)
