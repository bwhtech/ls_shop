import frappe

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import (
	add_item_group_links,
)
from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar.navbar_manager import (
	seed_menu_when_empty,
)
from ls_shop.utils import IN_CLAUSE_CHUNK_SIZE

CHILD_DOCTYPE = "Ecommerce Category Item Group"


def execute():
	"""Move the menu's item-group links off the standalone child table and onto the menu entry.

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
	"""The menu entries among ``names`` that actually link item groups."""
	entries = []
	for offset in range(0, len(names), IN_CLAUSE_CHUNK_SIZE):
		entries.extend(
			frappe.get_all(
				"Ecommerce Category",
				filters={"name": ["in", names[offset : offset + IN_CLAUSE_CHUNK_SIZE]]},
				fields=["name", "link_type"],
			)
		)
	# A type switch left the old rows behind, so rows under a Brand or URL entry are stale and
	# carrying them over would resurrect a link the shop owner had already replaced.
	return [entry for entry in entries if entry.link_type == "Item Group"]


def backfill_item_group_links():
	links = get_child_links()
	if not links:
		return

	entries = get_item_group_entries(list(links))
	add_item_group_links({entry.name: links[entry.name] for entry in entries})
	frappe.clear_document_cache("Ecommerce Category")


def drop_child_table():
	# Removing the doctype folder from the app leaves the DocType doc behind — migrate only ever
	# syncs the JSON files it finds — and deleting that doc does not take the table with it, so both
	# have to be asked for. The drop goes through the query builder rather than a literal statement
	# because MariaDB and Postgres quote the identifier differently.
	if frappe.db.exists("DocType", CHILD_DOCTYPE):
		frappe.delete_doc("DocType", CHILD_DOCTYPE, ignore_permissions=True)

	if frappe.db.table_exists(CHILD_DOCTYPE):
		frappe.db.sql_ddl(frappe.qb.drop_table(frappe.qb.DocType(CHILD_DOCTYPE)).if_exists().get_sql())
