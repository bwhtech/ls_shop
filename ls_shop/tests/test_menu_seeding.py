# Copyright (c) 2026, company@bwhstudios.com and Contributors
# See license.txt

"""The menu is a copy of the Item Group tree, taken once.

A fresh store gets one Ecommerce Category per Item Group so the storefront has navigation before
anyone opens the editor, and an existing store gets its `link_item_groups` rows moved onto the
single `item_group` link. After that the two trees are independent: the shop owner reorders, renames
and prunes the menu without any of it reaching the catalogue.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import get_root_of

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import get_menu_tree
from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar import navbar_manager
from ls_shop.patches import move_ecommerce_category_to_item_group_link as migration
from ls_shop.www.sitemap_segment import SEGMENT_CONFIG, get_segment_filters

PREFIX = "Test Seed"
LEGACY_CHILD_DOCTYPE = "Ecommerce Category Item Group"


def make_item_group(name, parent=None):
	return frappe.get_doc(
		{
			"doctype": "Item Group",
			"item_group_name": name,
			# ls_shop makes the storefront display name mandatory on Item Group.
			"custom_displayname": name,
			"parent_item_group": parent or get_root_of("Item Group"),
			"is_group": 1,
		}
	).insert()


def make_legacy_child_doctype():
	"""Rebuild the dropped child table so the migration runs against real rows, not a stand-in.

	`custom` keeps it in the database only. A regular DocType would write a JSON file back into the
	app folder that the test has no way to take back.
	"""
	if frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE):
		return

	frappe.get_doc(
		{
			"doctype": "DocType",
			"name": LEGACY_CHILD_DOCTYPE,
			"module": "Lifestyle Shop Ecommerce",
			"custom": 1,
			"istable": 1,
			"fields": [
				{
					"fieldname": "item_group",
					"fieldtype": "Link",
					"label": "Item Group",
					"options": "Item Group",
				}
			],
			"permissions": [],
		}
	).insert()


def add_legacy_link(category, item_group, idx):
	frappe.get_doc(
		{
			"doctype": LEGACY_CHILD_DOCTYPE,
			"parent": category,
			"parenttype": "Ecommerce Category",
			"parentfield": "link_item_groups",
			"item_group": item_group,
			"idx": idx,
		}
	).insert()


def find_node(nodes, name):
	for node in nodes:
		if node["name"] == name:
			return node
		found = find_node(node["children"], name)
		if found:
			return found
	return None


class TestMenuSeeding(IntegrationTestCase):
	def setUp(self):
		self.shoes = make_item_group(f"{PREFIX} Shoes").name
		self.sneakers = make_item_group(f"{PREFIX} Sneakers", self.shoes).name
		self.boots = make_item_group(f"{PREFIX} Boots", self.shoes).name

	def tearDown(self):
		# IntegrationTestCase rolls back once, after the whole class, so each test clears its own rows
		# to avoid duplicate-name collisions with the next test's setUp.
		if frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE):
			frappe.delete_doc("DocType", LEGACY_CHILD_DOCTYPE, ignore_permissions=True)
		frappe.db.delete("Ecommerce Category", {"name": ["like", f"{PREFIX}%"]})
		frappe.db.delete("Item Group", {"name": ["like", f"{PREFIX}%"]})
		frappe.local.ls_shop_storefront_menu = None

	def seeded_entries(self):
		return {
			entry.item_group: entry
			for entry in frappe.get_all(
				"Ecommerce Category",
				filters={"category_name": ["like", f"{PREFIX}%"]},
				fields=["name", "item_group", "parent_ecommerce_category", "is_group", "lft", "rgt"],
			)
		}

	def item_group_snapshot(self):
		return frappe.get_all(
			"Item Group",
			filters={"name": ["like", f"{PREFIX}%"]},
			fields=["name", "parent_item_group", "is_group", "lft", "rgt", "modified"],
			order_by="name asc",
		)

	def test_seeding_copies_the_item_group_tree_shape(self):
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		entries = self.seeded_entries()
		self.assertEqual(set(entries), {self.shoes, self.sneakers, self.boots})

		root = entries[self.shoes]
		self.assertFalse(root.parent_ecommerce_category)
		self.assertEqual(entries[self.sneakers].parent_ecommerce_category, root.name)
		self.assertEqual(entries[self.boots].parent_ecommerce_category, root.name)

		# A parent that ended up with children has to be marked a group, or the editor renders it as
		# a leaf and the storefront never opens the branch.
		self.assertEqual(root.is_group, 1)

	def test_seeding_gives_every_entry_valid_tree_bounds(self):
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		entries = self.seeded_entries()
		root = entries[self.shoes]
		# Bulk seeding suppresses per-row nested-set bookkeeping and rebuilds once at the end, so the
		# bounds are the thing most likely to be left at 0/0 by a regression here.
		self.assertGreater(root.rgt, root.lft)
		for item_group in (self.sneakers, self.boots):
			child = entries[item_group]
			self.assertGreater(child.lft, root.lft)
			self.assertLess(child.rgt, root.rgt)

	def test_seeding_twice_adds_nothing(self):
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)
		before = sorted(self.seeded_entries())

		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		self.assertEqual(sorted(self.seeded_entries()), before)

	def test_the_menu_and_the_catalogue_stay_independent(self):
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)
		before = self.item_group_snapshot()
		sneakers_entry = self.seeded_entries()[self.sneakers].name

		navbar_manager.update_node(sneakers_entry, display_name=f"{PREFIX} Trainers")
		navbar_manager.delete_node(self.seeded_entries()[self.boots].name)

		self.assertEqual(before, self.item_group_snapshot())
		self.assertTrue(frappe.db.exists("Item Group", self.boots))

	def test_a_new_item_group_does_not_appear_in_the_menu_on_its_own(self):
		"""The copy is a starting point, not a live mirror — only a re-import brings new groups in."""
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		sandals = make_item_group(f"{PREFIX} Sandals", self.shoes).name

		self.assertNotIn(sandals, self.seeded_entries())

	def test_install_seeds_the_menu_only_when_the_store_has_none(self):
		frappe.db.delete("Ecommerce Category")

		navbar_manager.seed_menu_when_empty()
		self.assertIn(self.shoes, self.seeded_entries())

		# A shop owner who built their own menu must not have the catalogue poured back into it.
		frappe.db.delete("Ecommerce Category")
		navbar_manager.create_node("", f"{PREFIX} Hand Built")

		navbar_manager.seed_menu_when_empty()
		self.assertNotIn(self.shoes, self.seeded_entries())

	def test_seeded_nested_entries_stay_out_of_the_sitemap(self):
		"""Seeding multiplies nested rows, and only a root carries a route — the rest emit no URL."""
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		routable = frappe.get_all(
			"Ecommerce Category",
			filters={
				**get_segment_filters(SEGMENT_CONFIG["collections"]),
				"category_name": ["like", f"{PREFIX}%"],
			},
			pluck="item_group",
		)

		self.assertEqual(routable, [self.shoes])


class TestLegacyItemGroupLinkMigration(IntegrationTestCase):
	def setUp(self):
		make_legacy_child_doctype()
		self.shirts = make_item_group(f"{PREFIX} Shirts").name
		self.belts = make_item_group(f"{PREFIX} Belts").name
		self.tab = navbar_manager.create_node("", f"{PREFIX} Menswear").name
		self.entry = navbar_manager.create_node(self.tab, f"{PREFIX} Tops", "Item Group", self.shirts).name
		# The migration reads the child rows, so the field it will fill has to start empty.
		frappe.db.set_value("Ecommerce Category", self.entry, "item_group", None)

	def tearDown(self):
		if frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE):
			frappe.delete_doc("DocType", LEGACY_CHILD_DOCTYPE, ignore_permissions=True)
		frappe.db.delete("Ecommerce Category", {"name": ["like", f"{PREFIX}%"]})
		frappe.db.delete("Item Group", {"name": ["like", f"{PREFIX}%"]})
		frappe.local.ls_shop_storefront_menu = None

	def siblings_of_entry(self):
		return frappe.get_all(
			"Ecommerce Category",
			filters={"parent_ecommerce_category": self.tab, "name": ["!=", self.entry]},
			pluck="item_group",
		)

	def test_the_linked_group_lands_on_the_entry(self):
		add_legacy_link(self.entry, self.shirts, 1)

		migration.execute()

		self.assertEqual(frappe.db.get_value("Ecommerce Category", self.entry, "item_group"), self.shirts)
		self.assertEqual(self.siblings_of_entry(), [])

	def test_extra_linked_groups_are_rehomed_as_siblings(self):
		"""One entry links one group now, and a dropped group would vanish from the navigation."""
		add_legacy_link(self.entry, self.shirts, 1)
		add_legacy_link(self.entry, self.belts, 2)

		migration.execute()

		self.assertEqual(frappe.db.get_value("Ecommerce Category", self.entry, "item_group"), self.shirts)
		self.assertEqual(self.siblings_of_entry(), [self.belts])

	def test_rows_left_behind_by_a_link_type_switch_are_ignored(self):
		"""A type switch never cleared the table, so those rows are a link the owner already replaced."""
		add_legacy_link(self.entry, self.shirts, 1)
		frappe.db.set_value("Ecommerce Category", self.entry, "link_type", "URL")

		migration.execute()

		self.assertIsNone(frappe.db.get_value("Ecommerce Category", self.entry, "item_group"))
		self.assertEqual(self.siblings_of_entry(), [])

	def test_the_migrated_menu_still_renders(self):
		add_legacy_link(self.entry, self.shirts, 1)

		migration.execute()

		node = find_node(get_menu_tree(), self.entry)
		self.assertEqual(node["item_group"], self.shirts)
		self.assertIn(f"subcategory={self.shirts.replace(' ', '%20')}", node["href"])

	def test_the_legacy_table_is_dropped(self):
		add_legacy_link(self.entry, self.shirts, 1)

		migration.execute()

		self.assertFalse(frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE))
		# Deleting the DocType does not take its table with it, and an orphan table survives every
		# later migrate — so the drop is the half of this that actually needs guarding.
		self.assertFalse(frappe.db.table_exists(LEGACY_CHILD_DOCTYPE))

	def test_running_the_migration_twice_changes_nothing(self):
		add_legacy_link(self.entry, self.shirts, 1)
		add_legacy_link(self.entry, self.belts, 2)

		migration.execute()
		after_first_run = frappe.get_all(
			"Ecommerce Category",
			filters={"category_name": ["like", f"{PREFIX}%"]},
			fields=["name", "item_group"],
			order_by="name asc",
		)

		migration.execute()

		self.assertEqual(
			frappe.get_all(
				"Ecommerce Category",
				filters={"category_name": ["like", f"{PREFIX}%"]},
				fields=["name", "item_group"],
				order_by="name asc",
			),
			after_first_run,
		)
