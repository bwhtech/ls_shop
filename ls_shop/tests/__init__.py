# Copyright (c) 2026, company@bwhstudios.com and Contributors
# See license.txt

"""Fixture helpers shared across the app's test suites."""

import frappe

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import (
	ITEM_GROUP_LINK_DOCTYPE,
)
from ls_shop.utils import IN_CLAUSE_CHUNK_SIZE


def delete_menu_entries(filters=None):
	"""Delete menu entries along with the item-group links hanging off them.

	`frappe.db.delete` never touches child rows, and an orphan link re-attaches to the next same-named entry.
	"""
	names = frappe.get_all("Ecommerce Category", filters=filters, pluck="name")
	for offset in range(0, len(names), IN_CLAUSE_CHUNK_SIZE):
		frappe.db.delete(
			ITEM_GROUP_LINK_DOCTYPE,
			{
				"parenttype": "Ecommerce Category",
				"parent": ["in", names[offset : offset + IN_CLAUSE_CHUNK_SIZE]],
			},
		)
	frappe.db.delete("Ecommerce Category", filters)
