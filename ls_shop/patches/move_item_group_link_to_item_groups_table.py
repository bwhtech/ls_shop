import frappe

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import (
	add_item_group_links,
)
from ls_shop.utils import IN_CLAUSE_CHUNK_SIZE

PARENT_DOCTYPE = "Ecommerce Category"
LEGACY_COLUMN = "item_group"


def execute():
	"""Move each menu entry's single item group onto the table that now holds any number of them.

	A menu entry links several item groups, so the one link that used to sit in a column moved into
	a child table. The column is read through the query builder because the field is gone from the
	DocType — `frappe.get_all` validates against that — and migrate leaves the column itself behind.
	"""
	if LEGACY_COLUMN not in frappe.db.get_table_columns(PARENT_DOCTYPE):
		return

	entries = get_legacy_links()
	if not entries:
		return

	add_item_group_links({entry.name: [entry.item_group] for entry in entries})
	# Clearing the column is what makes a second run a no-op: the rows it would copy are gone.
	clear_legacy_links([entry.name for entry in entries])
	frappe.clear_document_cache(PARENT_DOCTYPE)


def get_legacy_links():
	"""Menu entries still holding an item group in the dropped column."""
	category = frappe.qb.DocType(PARENT_DOCTYPE)
	return (
		frappe.qb.from_(category)
		.select(category.name, category.item_group)
		.where(category.item_group.notnull() & (category.item_group != ""))
		.run(as_dict=True)
	)


def clear_legacy_links(names):
	category = frappe.qb.DocType(PARENT_DOCTYPE)
	for offset in range(0, len(names), IN_CLAUSE_CHUNK_SIZE):
		chunk = names[offset : offset + IN_CLAUSE_CHUNK_SIZE]
		frappe.qb.update(category).set(category.item_group, None).where(category.name.isin(chunk)).run()
