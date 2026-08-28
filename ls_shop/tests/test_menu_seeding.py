# Copyright (c) 2026, company@bwhstudios.com and Contributors
# See license.txt

"""The menu is a copy of the Item Group tree, taken once.

A fresh store gets one Ecommerce Category per Item Group so the storefront has navigation before
anyone opens the editor, and an existing store gets its item-group links moved onto the entry's own
`item_groups` table — first from the standalone child table, then from the single link that briefly
replaced it. After that the two trees are independent: the shop owner reorders, renames and prunes
the menu without any of it reaching the catalogue.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils.nestedset import get_root_of

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import (
	get_item_groups_by_entry,
	get_menu_tree,
)
from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar import navbar_manager
from ls_shop.patches import move_ecommerce_category_to_item_group_link as child_table_migration
from ls_shop.patches import move_item_group_link_to_item_groups_table as single_link_migration
from ls_shop.tests import delete_menu_entries
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


def add_legacy_column():
	"""Restore the dropped `item_group` column so the migration runs against a real one.

	Left in place afterwards: dropping it is DDL on a shared test database, and an orphan column is
	exactly what a migrated site carries anyway — the migration only ever reads and clears it.
	"""
	if "item_group" not in frappe.db.get_table_columns("Ecommerce Category"):
		frappe.db.add_column("Ecommerce Category", "item_group", "Link")


def purge_stale_fixtures():
	"""The legacy migration drops a table, and DDL commits the open transaction in MariaDB. Anything
	this module wrote before that point survives the framework's end-of-class rollback — worse, the
	rollback then undoes tearDown's own deletes and resurrects it. Names are unique per test so a
	stale row can never collide, and this sweep keeps a developer's site from collecting them."""
	delete_menu_entries({"name": ["like", f"{PREFIX}%"]})
	frappe.db.delete("Item Group", {"name": ["like", f"{PREFIX}%"]})


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
		purge_stale_fixtures()
		# Unique per test: the class-wide rollback runs once at the end, and a sibling class in this
		# module commits mid-run, so a fixed name is a duplicate-key error waiting for the next run.
		self.prefix = f"{PREFIX} {frappe.generate_hash(length=8)}"
		self.shoes = make_item_group(f"{self.prefix} Shoes").name
		self.sneakers = make_item_group(f"{self.prefix} Sneakers", self.shoes).name
		self.boots = make_item_group(f"{self.prefix} Boots", self.shoes).name

	def tearDown(self):
		if frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE):
			frappe.delete_doc("DocType", LEGACY_CHILD_DOCTYPE, ignore_permissions=True)
		purge_stale_fixtures()
		frappe.local.ls_shop_storefront_menu = None

	def seeded_entries(self):
		"""The menu entries this test seeded, keyed by the item group each one links."""
		entries = frappe.get_all(
			"Ecommerce Category",
			filters={"category_name": ["like", f"{self.prefix}%"]},
			fields=["name", "parent_ecommerce_category", "is_group", "lft", "rgt"],
		)
		item_groups_by_entry = get_item_groups_by_entry([entry.name for entry in entries])
		return {
			item_groups_by_entry[entry.name][0]: entry
			for entry in entries
			if item_groups_by_entry.get(entry.name)
		}

	def item_group_snapshot(self):
		return frappe.get_all(
			"Item Group",
			filters={"name": ["like", f"{self.prefix}%"]},
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

		navbar_manager.update_node(sneakers_entry, display_name=f"{self.prefix} Trainers")
		navbar_manager.delete_node(self.seeded_entries()[self.boots].name)

		self.assertEqual(before, self.item_group_snapshot())
		self.assertTrue(frappe.db.exists("Item Group", self.boots))

	def test_a_new_item_group_does_not_appear_in_the_menu_on_its_own(self):
		"""The copy is a starting point, not a live mirror — only a re-import brings new groups in."""
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		sandals = make_item_group(f"{self.prefix} Sandals", self.shoes).name

		self.assertNotIn(sandals, self.seeded_entries())

	def test_install_seeds_the_menu_only_when_the_store_has_none(self):
		delete_menu_entries()

		navbar_manager.seed_menu_when_empty()
		self.assertIn(self.shoes, self.seeded_entries())

		# A shop owner who built their own menu must not have the catalogue poured back into it.
		delete_menu_entries()
		navbar_manager.create_node("", f"{self.prefix} Hand Built")

		navbar_manager.seed_menu_when_empty()
		self.assertNotIn(self.shoes, self.seeded_entries())

	def test_seeded_nested_entries_stay_out_of_the_sitemap(self):
		"""Seeding multiplies nested rows, and only a root carries a route — the rest emit no URL."""
		navbar_manager.seed_categories_from_item_groups(item_group=self.shoes)

		routable = frappe.get_all(
			"Ecommerce Category",
			filters={
				**get_segment_filters(SEGMENT_CONFIG["collections"]),
				"category_name": ["like", f"{self.prefix}%"],
			},
			pluck="name",
		)

		self.assertEqual(routable, [self.seeded_entries()[self.shoes].name])


class TestLegacyChildTableMigration(IntegrationTestCase):
	"""The standalone child table that once held the links moves onto the entry's own table."""

	def setUp(self):
		purge_stale_fixtures()
		self.prefix = f"{PREFIX} {frappe.generate_hash(length=8)}"
		make_legacy_child_doctype()
		self.shirts = make_item_group(f"{self.prefix} Shirts").name
		self.belts = make_item_group(f"{self.prefix} Belts").name
		self.tab = navbar_manager.create_node("", f"{self.prefix} Menswear").name
		self.entry = navbar_manager.create_node(
			self.tab, f"{self.prefix} Tops", "Item Group", self.shirts
		).name
		# The migration reads the legacy rows, so the table it will fill has to start empty.
		frappe.db.delete("Ecommerce Category Item Group Link", {"parent": self.entry})

	def tearDown(self):
		if frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE):
			frappe.delete_doc("DocType", LEGACY_CHILD_DOCTYPE, ignore_permissions=True)
		purge_stale_fixtures()
		frappe.local.ls_shop_storefront_menu = None

	def linked_item_groups(self):
		return get_item_groups_by_entry([self.entry]).get(self.entry, [])

	def siblings_of_entry(self):
		return frappe.get_all(
			"Ecommerce Category",
			filters={"parent_ecommerce_category": self.tab, "name": ["!=", self.entry]},
			pluck="name",
		)

	def test_the_linked_group_lands_on_the_entry(self):
		add_legacy_link(self.entry, self.shirts, 1)

		child_table_migration.execute()

		self.assertEqual(self.linked_item_groups(), [self.shirts])
		self.assertEqual(self.siblings_of_entry(), [])

	def test_every_linked_group_lands_on_the_same_entry(self):
		"""An entry links any number of groups, so none of them has to be rehomed elsewhere."""
		add_legacy_link(self.entry, self.shirts, 1)
		add_legacy_link(self.entry, self.belts, 2)

		child_table_migration.execute()

		self.assertEqual(self.linked_item_groups(), [self.shirts, self.belts])
		self.assertEqual(self.siblings_of_entry(), [])

	def test_rows_left_behind_by_a_link_type_switch_are_ignored(self):
		"""A type switch never cleared the table, so those rows are a link the owner already replaced."""
		add_legacy_link(self.entry, self.shirts, 1)
		frappe.db.set_value("Ecommerce Category", self.entry, "link_type", "URL")

		child_table_migration.execute()

		self.assertEqual(self.linked_item_groups(), [])
		self.assertEqual(self.siblings_of_entry(), [])

	def test_the_migrated_menu_still_renders(self):
		add_legacy_link(self.entry, self.shirts, 1)
		add_legacy_link(self.entry, self.belts, 2)

		child_table_migration.execute()

		node = find_node(get_menu_tree(), self.entry)
		self.assertEqual(node["item_groups"], [self.shirts, self.belts])
		self.assertIn(f"subcategory={self.shirts.replace(' ', '%20')}", node["href"])
		self.assertIn(f"{self.belts.replace(' ', '%20')}", node["href"])

	def test_the_legacy_table_is_dropped(self):
		add_legacy_link(self.entry, self.shirts, 1)

		child_table_migration.execute()

		self.assertFalse(frappe.db.exists("DocType", LEGACY_CHILD_DOCTYPE))
		# Deleting the DocType does not take its table with it, and an orphan table survives every
		# later migrate — so the drop is the half of this that actually needs guarding.
		self.assertFalse(frappe.db.table_exists(LEGACY_CHILD_DOCTYPE))

	def test_running_the_migration_twice_changes_nothing(self):
		add_legacy_link(self.entry, self.shirts, 1)
		add_legacy_link(self.entry, self.belts, 2)

		child_table_migration.execute()
		after_first_run = self.linked_item_groups()

		child_table_migration.execute()

		self.assertEqual(self.linked_item_groups(), after_first_run)


class TestSingleItemGroupLinkMigration(IntegrationTestCase):
	"""The single link that briefly replaced the child table moves onto the entry's own table."""

	def setUp(self):
		purge_stale_fixtures()
		self.prefix = f"{PREFIX} {frappe.generate_hash(length=8)}"
		self.shirts = make_item_group(f"{self.prefix} Shirts").name
		self.belts = make_item_group(f"{self.prefix} Belts").name
		self.tab = navbar_manager.create_node("", f"{self.prefix} Menswear").name
		self.entry = navbar_manager.create_node(self.tab, f"{self.prefix} Tops", "Item Group").name
		add_legacy_column()

	def tearDown(self):
		purge_stale_fixtures()
		frappe.local.ls_shop_storefront_menu = None

	def set_legacy_link(self, item_group):
		category = frappe.qb.DocType("Ecommerce Category")
		(
			frappe.qb.update(category)
			.set(category.item_group, item_group)
			.where(category.name == self.entry)
			.run()
		)

	def get_legacy_link(self):
		category = frappe.qb.DocType("Ecommerce Category")
		return (
			frappe.qb.from_(category)
			.select(category.item_group)
			.where(category.name == self.entry)
			.run(pluck=True)[0]
		)

	def linked_item_groups(self):
		return get_item_groups_by_entry([self.entry]).get(self.entry, [])

	def test_the_column_link_lands_on_the_entry(self):
		self.set_legacy_link(self.shirts)

		single_link_migration.execute()

		self.assertEqual(self.linked_item_groups(), [self.shirts])
		self.assertIsNone(self.get_legacy_link())

	def test_an_entry_that_already_links_groups_is_left_alone(self):
		"""The column is stale once the editor has written the table, and must not append to it."""
		navbar_manager.update_node(self.entry, link_type="Item Group", link_target=[self.shirts, self.belts])
		self.set_legacy_link(self.belts)

		single_link_migration.execute()

		self.assertEqual(self.linked_item_groups(), [self.shirts, self.belts])

	def test_running_the_migration_twice_changes_nothing(self):
		self.set_legacy_link(self.shirts)

		single_link_migration.execute()
		after_first_run = self.linked_item_groups()

		single_link_migration.execute()

		self.assertEqual(self.linked_item_groups(), after_first_run)
