# Copyright (c) 2026, hussain@buildwithhussain.com and Contributors
# See license.txt

import copy
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from ls_shop import utils
from ls_shop.search import build, record_builder, sync
from ls_shop.search import query as search_query
from ls_shop.search.engine_cache import clear_search_engine
from ls_shop.search.sqlite_product_search import SqliteProductSearch

TEST_INDEX_NAME = "test_ls_shop_product_search.db"
SEARCH_TOKEN = "zzwidget"
ARABIC_TERM = "قميص"
SHORT_TERM = "abc"

BRAND = "ZZ Test Search Brand"
ITEM_GROUP = "ZZ Test Search Group"
STYLE_ITEM = "ZZ-TEST-STYLE"
ITEM_ATTRIBUTE = "Zz Test Color"
CATEGORY_NAME = "Zz Test Category"
NON_PRIVILEGED_USER = "zz_test_search_user@example.com"


class TestStorefrontSearch(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.original_index_name = SqliteProductSearch.INDEX_NAME
		cls.original_indexable = SqliteProductSearch.INDEXABLE_DOCTYPES
		SqliteProductSearch.INDEX_NAME = TEST_INDEX_NAME
		SqliteProductSearch().drop_index()

		settings = frappe.get_cached_doc("Lifestyle Settings")
		cls.default_price_list = settings.default_price_list
		cls.sale_price_list = settings.sale_price_list
		cls.price_names = {}

		cls.drop_catalogue()
		cls.build_catalogue()
		cls.scope_index_to_fixtures()
		cls.ensure_non_privileged_user()
		# The fixtures outlive a single test method (each test rebuilds the index from them), so they
		# are committed and torn down explicitly rather than riding the per-test transaction.
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		cls.drop_catalogue()
		frappe.db.commit()
		SqliteProductSearch().drop_index()
		SqliteProductSearch.INDEX_NAME = cls.original_index_name
		SqliteProductSearch.INDEXABLE_DOCTYPES = cls.original_indexable
		super().tearDownClass()

	def setUp(self):
		# frappe.local persists across test methods, so a memoized index_exists() from a prior test would
		# leak into test_index_missing_falls_back_without_throw. Reset the request-scoped engine per test.
		clear_search_engine()
		self.rebuild_index()

	# -- fixtures --------------------------------------------------------------------------------

	@classmethod
	def drop_catalogue(cls):
		"""Remove any fixtures left behind by an aborted run so setUpClass is re-runnable."""
		for doctype, filters in (
			("Item Price", {"item_code": ("like", "ZZ-%")}),
			("Style Attribute Variant", {"item_style": STYLE_ITEM}),
			("Style Attribute Configurator", {"item_template": STYLE_ITEM}),
			("Ecommerce Category", {"category_name": CATEGORY_NAME}),
			("Item", {"item_group": ITEM_GROUP}),
			("Item Group", {"name": ITEM_GROUP}),
			("Item Attribute", {"name": ITEM_ATTRIBUTE}),
			("Brand", {"name": BRAND}),
		):
			for name in frappe.get_all(doctype, filters=filters, pluck="name"):
				frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	def unpublish(self, variant_name):
		"""Unpublish a variant for the duration of one test, restoring it afterwards."""
		frappe.db.set_value("Style Attribute Variant", variant_name, "is_published", 0)
		self.addCleanup(frappe.db.set_value, "Style Attribute Variant", variant_name, "is_published", 1)

	@classmethod
	def build_catalogue(cls):
		cls.ensure_item_group()
		cls.ensure_brand()
		cls.ensure_item_attribute()
		cls.ensure_item(STYLE_ITEM, "Zzwidget Style Template", brand=BRAND)

		configurator = frappe.get_doc(
			{
				"doctype": "Style Attribute Configurator",
				"item_template": STYLE_ITEM,
				"item_attribute": ITEM_ATTRIBUTE,
			}
		).insert(ignore_permissions=True)

		# red: discounted + cheapest; blue: pricier, no discount. Both indexed.
		cls.red = cls.make_variant(
			configurator.name,
			color="Zzred",
			display_name="Zzwidget Premium Red",
			sizes=[("ZS", "ZZ-RED-S", 100, 80), ("ZM", "ZZ-RED-M", 120, 90)],
		)
		cls.blue = cls.make_variant(
			configurator.name,
			color="Zzblue",
			display_name="Zzwidget Premium Blue",
			sizes=[("ZS", "ZZ-BLUE-S", 200, None), ("ZM", "ZZ-BLUE-M", 220, None)],
		)
		# green: published but deliberately left OUT of the index scope, so a name that exists in
		# MariaDB but not in the index never leaks into an FTS result.
		cls.green = cls.make_variant(
			configurator.name,
			color="Zzgreen",
			display_name="Zzwidget Premium Green",
			sizes=[("ZS", "ZZ-GREEN-S", 150, None)],
		)
		cls.category = (
			frappe.get_doc(
				{
					"doctype": "Ecommerce Category",
					"category_name": CATEGORY_NAME,
					"display_name": "Zzwidget Test Category",
					"route_slug": "zz-test-category",
					"enabled": 1,
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	@classmethod
	def scope_index_to_fixtures(cls):
		scoped = copy.deepcopy(SqliteProductSearch.INDEXABLE_DOCTYPES)
		scoped["Style Attribute Variant"]["filters"] = {
			"is_published": 1,
			"name": ("in", [cls.red, cls.blue]),
		}
		scoped["Ecommerce Category"]["filters"] = {"enabled": 1, "name": ("in", [cls.category])}
		SqliteProductSearch.INDEXABLE_DOCTYPES = scoped

	@classmethod
	def make_variant(cls, configurator, color, display_name, sizes):
		"""Create one published Style Attribute Variant + its size SKUs + Item Prices."""
		for _label, item_code, default_rate, sale_rate in sizes:
			cls.ensure_item(item_code, f"{display_name} {item_code}")
			cls.make_price(item_code, cls.default_price_list, default_rate)
			if sale_rate is not None:
				cls.make_price(item_code, cls.sale_price_list, sale_rate)

		variant = frappe.get_doc(
			{
				"doctype": "Style Attribute Variant",
				"configurator": configurator,
				"item_style": STYLE_ITEM,
				"attribute_value": color,
				"attribute_name": color,
				"display_name": display_name,
				"item_group": ITEM_GROUP,
				"is_published": 1,
				"images": [{"image": "/files/zz-a.png"}, {"image": "/files/zz-b.png"}],
				"sizes": [{"size": label, "item_code": item_code} for label, item_code, _d, _s in sizes],
			}
		).insert(ignore_permissions=True)
		return variant.name

	@classmethod
	def make_price(cls, item_code, price_list, rate):
		price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": price_list,
				"price_list_rate": rate,
			}
		).insert(ignore_permissions=True)
		cls.price_names[(item_code, price_list)] = price.name

	@classmethod
	def ensure_item(cls, item_code, item_name, brand=None):
		if frappe.db.exists("Item", item_code):
			return
		doc = {
			"doctype": "Item",
			"item_code": item_code,
			"item_name": item_name,
			"item_group": ITEM_GROUP,
			"stock_uom": "Nos",
			"is_stock_item": 1,
		}
		if brand:
			doc["brand"] = brand
		frappe.get_doc(doc).insert(ignore_permissions=True)

	@classmethod
	def ensure_item_group(cls):
		if not frappe.db.exists("Item Group", ITEM_GROUP):
			frappe.get_doc(
				{
					"doctype": "Item Group",
					"item_group_name": ITEM_GROUP,
					"is_group": 0,
					"parent_item_group": "All Item Groups",
					# ls_shop customises Item Group with two mandatory storefront display names.
					"custom_displayname": ITEM_GROUP,
					"custom_item_group_display_name": ITEM_GROUP,
				}
			).insert(ignore_permissions=True)

	@classmethod
	def ensure_brand(cls):
		if not frappe.db.exists("Brand", BRAND):
			frappe.get_doc({"doctype": "Brand", "brand": BRAND}).insert(ignore_permissions=True)

	@classmethod
	def ensure_item_attribute(cls):
		if not frappe.db.exists("Item Attribute", ITEM_ATTRIBUTE):
			frappe.get_doc(
				{
					"doctype": "Item Attribute",
					"attribute_name": ITEM_ATTRIBUTE,
					"item_attribute_values": [{"attribute_value": "Zzred", "abbr": "ZZR"}],
				}
			).insert(ignore_permissions=True)

	@classmethod
	def ensure_non_privileged_user(cls):
		"""A User with no System Manager role, to prove the rebuild endpoint rejects low-privilege callers."""
		if not frappe.db.exists("User", NON_PRIVILEGED_USER):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": NON_PRIVILEGED_USER,
					"first_name": "Zz Test Search User",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)

	def rebuild_index(self):
		engine = SqliteProductSearch()
		engine.drop_index()
		engine.build_index()

	# -- search vs frappe.qb dispatch ------------------------------------------------------------

	def test_latin_search_uses_sqlite(self):
		self.assertTrue(search_query.relevance_sort_available({"search": SEARCH_TOKEN}))
		self.assertFalse(search_query.use_qb_fallback({"search": SEARCH_TOKEN}))

		names = SqliteProductSearch().search(SEARCH_TOKEN)["product_names"]
		self.assertIn(self.red, names)
		self.assertIn(self.blue, names)
		# green is published but not indexed, so the FTS path never surfaces it.
		self.assertNotIn(self.green, names)

		cards = search_query.storefront_search(SEARCH_TOKEN, limit=6)["products"]
		self.assertEqual({card["name"] for card in cards}, {self.red, self.blue})

	def test_arabic_search_falls_back_to_qb(self):
		self.assertTrue(search_query.use_qb_fallback({"search": ARABIC_TERM}))

	def test_short_term_falls_back_to_qb(self):
		self.assertTrue(search_query.use_qb_fallback({"search": SHORT_TERM}))

	def test_browse_without_term_stays_on_qb(self):
		self.assertTrue(search_query.use_qb_fallback({}))
		self.assertIsNone(search_query.listing_facets({}))

	def test_edit_distance_fallback_corrects_short_typo(self):
		# Trigram Jaccard alone leaves "zzwidgt" uncorrected; the Levenshtein fallback catches it.
		result = SqliteProductSearch().search("zzwidgt")
		self.assertEqual(result["corrected_words"].get("zzwidgt"), SEARCH_TOKEN)
		self.assertEqual(set(result["product_names"]), {self.red, self.blue})

	# -- facets ----------------------------------------------------------------------------------

	def test_facets_reflect_indexed_catalogue(self):
		facets = SqliteProductSearch().search(SEARCH_TOKEN)["facets"]
		self.assertEqual(facets["brand"].get(BRAND), 2)
		self.assertEqual(set(facets["color"]), {"Zzred", "Zzblue"})
		self.assertEqual(facets["size"].get("ZS"), 2)
		self.assertEqual(facets["size"].get("ZM"), 2)

		sidebar = search_query.listing_facets({"search": SEARCH_TOKEN})
		self.assertIn(BRAND, sidebar["brands"])
		self.assertEqual(set(sidebar["colors"]), {"Zzred", "Zzblue"})

	# -- filter / sort / pagination / count parity -----------------------------------------------

	def test_price_and_discount_filters(self):
		engine = SqliteProductSearch()
		# red effective 80 (sale), blue effective 200 (no sale).
		self.assertEqual(engine.search_products({"search": SEARCH_TOKEN, "min_price": 150}), [self.blue])
		self.assertEqual(engine.search_products({"search": SEARCH_TOKEN, "max_price": 100}), [self.red])
		self.assertEqual(engine.search_products({"search": SEARCH_TOKEN, "has_discount": 1}), [self.red])
		self.assertEqual(engine.search_count({"search": SEARCH_TOKEN, "min_price": 150}), 1)

	def test_sort_pagination_and_count_parity(self):
		engine = SqliteProductSearch()
		filters = {"search": SEARCH_TOKEN}
		self.assertEqual(
			engine.search_products(filters, sort_by="price_low", page_length=50), [self.red, self.blue]
		)
		self.assertEqual(
			engine.search_products(filters, sort_by="price_high", page_length=50), [self.blue, self.red]
		)

		page_1 = engine.search_products(filters, sort_by="price_low", page=1, page_length=1)
		page_2 = engine.search_products(filters, sort_by="price_low", page=2, page_length=1)
		self.assertEqual(page_1, [self.red])
		self.assertEqual(page_2, [self.blue])

		# The count drives the pagination controls, so it must equal the rows you can page to.
		matched = engine.search_products(filters, page_length=50)
		self.assertEqual(engine.search_count(filters), len(matched))
		self.assertEqual(len(matched), 2)

	def test_grid_preserves_engine_rank(self):
		cards = utils.get_product_list({"search": SEARCH_TOKEN})
		ranked = SqliteProductSearch().search_products({"search": SEARCH_TOKEN})
		self.assertEqual([card["name"] for card in cards], ranked)

	def test_total_count_uses_engine_for_search(self):
		self.assertEqual(utils.get_total_product_count({"search": SEARCH_TOKEN}), 2)

	# -- live price overlay ----------------------------------------------------------------------

	def test_live_price_overlay_reflects_item_price_edit(self):
		# The indexed red sale price is 80; editing the live Item Price must show up on the card without
		# a rebuild, because an Item Price edit fires no Style Attribute Variant event.
		price_name = self.price_names[("ZZ-RED-S", self.sale_price_list)]
		frappe.db.set_value("Item Price", price_name, "price_list_rate", 50)
		self.addCleanup(frappe.db.set_value, "Item Price", price_name, "price_list_rate", 80)

		card = search_query.build_product_cards([self.red])[0]
		self.assertEqual(card["sale_price"], 50)
		self.assertEqual(card["default_price"], 100)

	# -- gotcha: unpublishing must REMOVE, not merely skip ----------------------------------------

	def test_unpublishing_removes_variant_from_index(self):
		engine = SqliteProductSearch()
		self.assertIn(self.red, engine.search(SEARCH_TOKEN)["product_names"])

		self.unpublish(self.red)
		engine.index_docs("Style Attribute Variant", [self.red])

		self.assertEqual(engine.search(SEARCH_TOKEN)["product_names"], [self.blue])
		self.assertEqual(engine.hydrate_cards([self.red]), [])
		self.assertEqual(
			engine.sql(
				"SELECT COUNT(*) AS count FROM search_size WHERE doc_id = ?",
				(f"Style Attribute Variant:{self.red}",),
				read_only=True,
			)[0]["count"],
			0,
		)

	def test_disabled_category_is_removed_from_index(self):
		engine = SqliteProductSearch()
		self.assertIn(self.category, engine.search(SEARCH_TOKEN)["category_names"])

		frappe.db.set_value("Ecommerce Category", self.category, "enabled", 0)
		self.addCleanup(frappe.db.set_value, "Ecommerce Category", self.category, "enabled", 1)
		engine.index_docs("Ecommerce Category", [self.category])

		self.assertEqual(engine.search(SEARCH_TOKEN)["category_names"], [])

	def test_index_doc_removes_a_single_unpublished_variant(self):
		engine = SqliteProductSearch()
		self.unpublish(self.red)
		engine.index_doc("Style Attribute Variant", self.red)
		self.assertNotIn(self.red, engine.search(SEARCH_TOKEN)["product_names"])

	# -- gotcha: bulk frappe.db.set_value writes fire no doc event ---------------------------------

	def test_bulk_publish_hands_names_to_the_index(self):
		bulk = frappe.get_doc({"doctype": "Bulk Publish Variants", "brand": BRAND})
		for variant in (self.red, self.blue):
			self.addCleanup(frappe.db.set_value, "Style Attribute Variant", variant, "is_published", 1)
		with patch("ls_shop.search.sync.frappe.enqueue") as enqueue:
			bulk.bulk_toggle_publish(publish=False, style_attribute_variant_list=[self.red, self.blue])

		self.assertEqual(frappe.db.get_value("Style Attribute Variant", self.red, "is_published"), 0)
		enqueue.assert_called_once()
		_args, kwargs = enqueue.call_args
		self.assertEqual(kwargs["doctype"], "Style Attribute Variant")
		self.assertEqual(set(kwargs["names"]), {self.red, self.blue})

	def test_batch_sync_is_blind_to_in_import(self):
		# An importer sets in_import to silence per-doc events, then hands the whole set over once;
		# honouring the flag here would swallow that replacement sync.
		with patch.dict(frappe.flags, {"in_import": True}):
			self.assertTrue(sync.skip_sync())
			self.assertFalse(sync.skip_batch_sync())

	def test_batch_sync_is_skipped_during_migrate(self):
		with patch.dict(frappe.flags, {"in_migrate": True}):
			self.assertTrue(sync.skip_batch_sync())

	def test_enqueue_upsert_many_chunks_long_name_lists(self):
		names = [f"zz-name-{index}" for index in range(record_builder.IN_CLAUSE_CHUNK_SIZE + 1)]
		with patch("ls_shop.search.sync.frappe.enqueue") as enqueue:
			sync.enqueue_upsert_many("Style Attribute Variant", names)
		self.assertEqual(enqueue.call_count, 2)
		self.assertEqual(sum(len(call.kwargs["names"]) for call in enqueue.call_args_list), len(names))

	def test_upsert_docs_bootstraps_a_missing_index(self):
		SqliteProductSearch().drop_index()
		with patch("ls_shop.search.sync.ensure_index_built") as ensure:
			sync.upsert_docs("Style Attribute Variant", [self.red])
		ensure.assert_called_once()

	# -- configurable content resolution -----------------------------------------------------------

	def set_content_fields(self, pairs):
		"""Point Lifestyle Settings.search_content_fields at the given (doctype, field) pairs."""
		frappe.clear_document_cache("Lifestyle Settings")
		self.addCleanup(frappe.clear_document_cache, "Lifestyle Settings")
		settings = frappe.get_single("Lifestyle Settings")
		settings.search_content_fields = []
		for search_doctype, field in pairs:
			settings.append("search_content_fields", {"search_doctype": search_doctype, "field": field})
		with patch("frappe.enqueue"):
			settings.save(ignore_permissions=True)
		frappe.clear_document_cache("Lifestyle Settings")

	def content_for(self, variant_name):
		return record_builder.build_product_search_records([variant_name])[0]["content"]

	def test_configurator_field_flows_into_content(self):
		# An SAC field (item_attribute, reachable via variant.configurator) must reach the variant's content.
		self.set_content_fields([("Style Attribute Configurator", "item_attribute")])
		self.assertEqual(self.content_for(self.red), ITEM_ATTRIBUTE)

	def test_non_text_and_missing_fields_are_skipped(self):
		# is_published is a Check (non-text) and there is no such column as `not_a_real_field`; both are
		# dropped, leaving only the valid Item.brand pair in content.
		self.set_content_fields(
			[
				("Item", "brand"),
				("Style Attribute Variant", "is_published"),
				("Item", "not_a_real_field"),
			]
		)
		self.assertEqual(self.content_for(self.red), BRAND)

	def test_disallowed_doctype_is_skipped(self):
		self.set_content_fields([("Item", "brand"), ("Sales Order", "customer")])
		self.assertEqual(self.content_for(self.red), BRAND)

	def test_empty_config_falls_back_to_defaults(self):
		self.set_content_fields([])
		self.assertEqual(self.content_for(self.red), f"Zzwidget Premium Red Zzred {ITEM_GROUP} {BRAND}")

	# -- install/migrate bootstrap & nightly rebuild -------------------------------------------------

	def test_ensure_index_built_noop_when_present(self):
		with patch("frappe.enqueue") as enqueue:
			build.ensure_index_built()
		enqueue.assert_not_called()

	def test_ensure_index_built_enqueues_when_absent(self):
		SqliteProductSearch().drop_index()
		with patch("frappe.enqueue") as enqueue:
			build.ensure_index_built()
		enqueue.assert_called_once()
		_args, kwargs = enqueue.call_args
		self.assertEqual(kwargs["queue"], "long")
		self.assertIs(kwargs["force"], False)
		self.assertEqual(kwargs["job_id"], build.SEARCH_CLASS_PATH)
		self.assertTrue(kwargs["deduplicate"])

	def test_ensure_index_built_noop_on_empty_catalogue(self):
		SqliteProductSearch().drop_index()
		with patch("frappe.db.exists", return_value=False), patch("frappe.enqueue") as enqueue:
			build.ensure_index_built()
		enqueue.assert_not_called()

	def test_nightly_rebuild_is_unconditional(self):
		# Enqueues a forced rebuild with no index-existence guard, and leaves the index live: build_index
		# swaps a fresh temp DB over it, so there is no pre-drop.
		with patch.object(SqliteProductSearch, "drop_index") as drop, patch("frappe.enqueue") as enqueue:
			build.rebuild_index_nightly()
		drop.assert_not_called()
		enqueue.assert_called_once()
		_args, kwargs = enqueue.call_args
		self.assertEqual(kwargs["queue"], "long")
		self.assertIs(kwargs["force"], True)

	# -- fallback safety net -------------------------------------------------------------------------

	def test_index_missing_falls_back_without_throw(self):
		SqliteProductSearch().drop_index()
		clear_search_engine()
		self.assertTrue(search_query.use_qb_fallback({"search": SEARCH_TOKEN}))
		# A live search must degrade to frappe.qb, not raise, when the index is gone.
		self.assertIsInstance(utils.get_product_list({"search": SEARCH_TOKEN}), list)

	# -- endpoint hardening --------------------------------------------------------------------------

	def test_rebuild_index_requires_system_manager(self):
		# frappe.only_for early-returns under frappe.flags.in_test, so toggle it off to exercise the guard.
		frappe.flags.in_test = False
		try:
			frappe.set_user(NON_PRIVILEGED_USER)
			self.assertRaises(frappe.PermissionError, build.rebuild_index)
		finally:
			frappe.set_user("Administrator")
			frappe.flags.in_test = True
