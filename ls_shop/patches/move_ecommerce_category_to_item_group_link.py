import frappe
from frappe.query_builder import Case

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar.navbar_manager import (
	create_node,
	seed_categories_from_item_groups,
)
from ls_shop.utils import IN_CLAUSE_CHUNK_SIZE

CHILD_DOCTYPE = "Ecommerce Category Item Group"


def execute():
	"""Move the menu's item-group links off the child table and onto a single link per entry.

	Run in this order: an existing site's links have to land on the new field before the table that
	holds them is dropped, and the tree may only be seeded once it is clear the site has no menu of
	its own to lose.
	"""
	backfill_item_group_links()
	seed_menu_when_empty()
	drop_child_table()


def get_child_links():
	"""Item groups each menu entry links, in editor order, keyed by entry.

	Read through the DocType rather than the table so a site that already ran this patch — and a
	fresh install, where the child table never existed — falls straight through.
	"""
	if not frappe.db.exists("DocType", CHILD_DOCTYPE):
		return {}

	links = {}
	for row in frappe.get_all(
		CHILD_DOCTYPE,
		filters={"parenttype": "Ecommerce Category"},
		fields=["parent", "item_group"],
		order_by="parent asc, idx asc",
	):
		if row.item_group:
			links.setdefault(row.parent, []).append(row.item_group)
	return links


def get_item_group_entries(names):
	"""The menu entries among ``names`` that actually link item groups, with their parent."""
	entries = []
	for offset in range(0, len(names), IN_CLAUSE_CHUNK_SIZE):
		entries.extend(
			frappe.get_all(
				"Ecommerce Category",
				filters={"name": ["in", names[offset : offset + IN_CLAUSE_CHUNK_SIZE]]},
				fields=["name", "parent_ecommerce_category", "link_type"],
			)
		)
	# A type switch left the old rows behind, so rows under a Brand or URL entry are stale and
	# carrying them over would resurrect a link the shop owner had already replaced.
	return [entry for entry in entries if entry.link_type == "Item Group"]


def set_item_group_links(item_group_for_entry):
	category = frappe.qb.DocType("Ecommerce Category")
	names = list(item_group_for_entry)

	for offset in range(0, len(names), IN_CLAUSE_CHUNK_SIZE):
		chunk = names[offset : offset + IN_CLAUSE_CHUNK_SIZE]
		item_group = Case()
		for name in chunk:
			item_group = item_group.when(category.name == name, item_group_for_entry[name])

		(
			frappe.qb.update(category)
			.set(category.item_group, item_group)
			.where(category.name.isin(chunk))
			.run()
		)

	if names:
		frappe.clear_document_cache("Ecommerce Category")


def add_sibling_entries(entry, item_groups):
	"""Rehome the item groups beyond the first as siblings of the entry that linked them.

	One entry now links one group, and silently dropping the rest would take those products out of
	the navigation. A sibling sits at the entry's own depth, so it is always within the menu depth
	cap, and it keeps the group one click from where the shop owner put it.
	"""
	for item_group in item_groups:
		create_node(entry.parent_ecommerce_category or "", item_group, "Item Group", item_group)


def backfill_item_group_links():
	links = get_child_links()
	if not links:
		return

	entries = get_item_group_entries(list(links))
	set_item_group_links({entry.name: links[entry.name][0] for entry in entries})

	for entry in entries:
		add_sibling_entries(entry, links[entry.name][1:])


def seed_menu_when_empty():
	"""A site that never built a menu gets the Item Group tree copied in, the way a fresh install does."""
	if frappe.db.count("Ecommerce Category"):
		return

	seed_categories_from_item_groups()


def drop_child_table():
	# Removing the doctype folder from the app leaves the DocType doc and its table behind — migrate
	# only ever syncs the JSON files it finds — so the delete has to be asked for.
	if frappe.db.exists("DocType", CHILD_DOCTYPE):
		frappe.delete_doc("DocType", CHILD_DOCTYPE, ignore_permissions=True)
