import frappe

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar.navbar_manager import (
	seed_menu_when_empty,
)


def execute():
	"""Seed a store that has no menu of its own from its Item Group tree.

	This patch used to fold the entry's `link_item_groups` rows down to a single item group and drop
	the table holding them. A menu entry links several groups again, so that table is the shape the
	app is back on: folding it would throw the extra groups away, and dropping it would take a live
	table with it. Both steps are gone; the seeding is what is left worth running.

	The module keeps its name deliberately — renaming it would re-run it on every site that has
	already recorded it, and re-seeding a menu the shop owner emptied on purpose is the one thing
	`seed_menu_when_empty` exists to avoid.
	"""
	seed_menu_when_empty()
