# Copyright (c) 2026, ivend and Contributors
# Theme engine tests: name validation + path containment (unit), inheritance + asset
# resolution + routing + the two anti-regression contracts (shadow audit, SEO block
# contract) that guard the menu manager/footer editor and the SEO pipeline (real-DB).

import os
import re

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import (
	build_theme_context,
	get_contained_path,
	get_theme_names,
	is_within_directory,
	validate_theme_name,
)
from ls_shop.shop_themes.doctype.shop_theme_settings.shop_theme_settings import (
	build_compiled_routes,
	seed_default_routes,
)
from ls_shop.shop_themes.jinja_helpers import shop_theme_asset_url, shop_theme_config
from ls_shop.shop_themes.theme_resolver import (
	find_theme_file,
	is_dynamic_page,
	match_route,
)

APP_PATH = frappe.get_app_path("ls_shop")
THEMES_ROOT = os.path.join(APP_PATH, "themes")


class UnitTestShopTheme(UnitTestCase):
	def test_theme_name_pattern_rejects_path_separators(self):
		self.assertRaises(frappe.ValidationError, validate_theme_name, "../etc/passwd")
		self.assertRaises(frappe.ValidationError, validate_theme_name, "foo/bar")

	def test_theme_name_pattern_accepts_letters_numbers_spaces_hyphens_underscores(self):
		validate_theme_name("Shop Default Theme")
		validate_theme_name("shop-default_theme 2")

	def test_is_within_directory_rejects_sibling_prefix_directories(self):
		self.assertFalse(is_within_directory("/tmp/themes/foo", "/tmp/themes/foo_evil"))
		self.assertTrue(is_within_directory("/tmp/themes/foo", "/tmp/themes/foo/pages/x.html"))

	def test_is_within_directory_rejects_traversal(self):
		self.assertFalse(is_within_directory("/tmp/themes/foo", "/tmp/themes/foo/../foo_evil/x"))

	def test_get_contained_path_throws_on_escape(self):
		self.assertRaises(frappe.ValidationError, get_contained_path, "/tmp/themes/foo", "..", "foo_evil")

	def test_find_theme_file_containment_checks_every_candidate(self):
		self.assertIsNone(find_theme_file(["/tmp/themes/foo"], "../foo_evil/secret.py"))


class IntegrationTestShopTheme(IntegrationTestCase):
	def test_get_theme_names_walks_child_first_and_guards_cycles(self):
		# Exercised end-to-end against the shipped reference theme rather than mocked, since
		# the whole point under test is the real inheritance chain.
		names = get_theme_names("Shop Default Theme")
		self.assertEqual(names, ["Shop Default Theme", "Shop Base Theme"])

	def setUp(self):
		self.settings = frappe.get_single("Shop Theme Settings")
		self.original_active_theme = self.settings.active_theme
		self.original_dynamic_pages_enabled = self.settings.dynamic_pages_enabled

	def tearDown(self):
		frappe.db.set_single_value("Shop Theme Settings", "active_theme", self.original_active_theme)
		frappe.db.set_single_value(
			"Shop Theme Settings", "dynamic_pages_enabled", self.original_dynamic_pages_enabled
		)
		frappe.clear_cache()

	def activate(self, theme_name):
		frappe.db.set_single_value("Shop Theme Settings", "active_theme", theme_name)
		frappe.clear_cache()

	def test_build_theme_context_resolves_the_inheritance_chain_and_dirs(self):
		context = build_theme_context("Shop Default Theme")
		self.assertEqual(context["names"], ["Shop Default Theme", "Shop Base Theme"])
		self.assertTrue(all(os.path.isdir(theme_dir) for theme_dir in context["dirs"]))

	def test_build_theme_context_is_empty_for_no_theme(self):
		context = build_theme_context(None)
		self.assertIsNone(context["theme_name"])
		self.assertEqual(context["dirs"], [])

	def test_asset_url_falls_back_to_the_active_child_theme_not_the_root_ancestor(self):
		self.activate("Shop Default Theme")
		url = shop_theme_asset_url("no/such/file.css")
		self.assertIn("/themes/shop_default_theme/", url)
		self.assertNotIn("/themes/shop_base_theme/", url)

	def test_asset_url_resolves_an_asset_owned_by_the_parent_base_theme(self):
		self.activate("Shop Default Theme")
		url = shop_theme_asset_url("images/placeholder.svg")
		self.assertIn("/themes/shop_base_theme/images/placeholder.svg", url)

	def test_asset_url_is_empty_with_no_active_theme(self):
		self.activate(None)
		self.assertEqual(shop_theme_asset_url("images/placeholder.svg"), "")

	def test_theme_config_returns_empty_dict_when_theme_has_no_settings_doctype(self):
		self.activate("Shop Base Theme")
		self.assertEqual(shop_theme_config(), frappe._dict())

	def test_theme_config_returns_the_settings_single_for_the_active_theme(self):
		self.activate("Shop Default Theme")
		config = shop_theme_config()
		self.assertEqual(config.doctype, "Shop Default Theme Settings")

	def test_route_table_compiles_and_matches_named_groups(self):
		compiled = build_compiled_routes()
		matched_route, match = match_route(compiled["routes"], "en/products/some-slug")
		self.assertIsNotNone(matched_route)
		self.assertEqual(matched_route["template_path"], "pages/products/details.html")
		self.assertEqual(match.group("route"), "some-slug")

	def test_route_table_no_match_for_unknown_path(self):
		compiled = build_compiled_routes()
		matched_route, _match = match_route(compiled["routes"], "en/not-a-real-route")
		self.assertIsNone(matched_route)

	def test_invalid_regex_in_a_route_throws_on_save(self):
		settings = frappe.get_single("Shop Theme Settings")
		settings.append("routes", {"url_pattern": "(unterminated", "template_path": "pages/x.html"})
		self.assertRaises(frappe.ValidationError, settings.save)

	def test_seed_default_routes_is_idempotent_on_url_pattern(self):
		count_before = frappe.db.count("Shop Themed Route")
		seed_default_routes()
		self.assertEqual(frappe.db.count("Shop Themed Route"), count_before)

	def test_seed_default_routes_never_reenables_dynamic_pages(self):
		frappe.db.set_single_value("Shop Theme Settings", "dynamic_pages_enabled", 0)
		seed_default_routes()
		self.assertEqual(frappe.db.get_single_value("Shop Theme Settings", "dynamic_pages_enabled"), 0)

	def test_is_dynamic_page_rejects_reserved_first_segments(self):
		settings = {"dynamic_pages_enabled": True}
		self.assertFalse(is_dynamic_page(settings, "api/method/x"))

	def test_is_dynamic_page_requires_a_known_language_prefix(self):
		settings = {"dynamic_pages_enabled": True}
		self.assertFalse(is_dynamic_page(settings, "not-a-lang/foo"))
		self.assertTrue(is_dynamic_page(settings, "en/foo"))

	def test_is_dynamic_page_off_when_disabled(self):
		settings = {"dynamic_pages_enabled": False}
		self.assertFalse(is_dynamic_page(settings, "en/foo"))


class IntegrationTestThemeShadowAudit(IntegrationTestCase):
	"""§9.4 - the most dangerous failure mode: a theme shipping its own copy of a shared
	include silently disconnects the menu manager and footer editor with no error."""

	def is_one_line_passthrough(self, absolute_path, app_relative_path):
		# The theme contract requires exactly this shape for header/footer: a bare
		# {% include "templates/<same path>" %} that delegates instead of duplicating. That
		# is safe by construction - the loader still serves the real templates/ file, this
		# file just forwards to it - so it is not a shadow.
		with open(absolute_path) as theme_file:
			content = theme_file.read().strip()
		expected = '{%% include "templates/%s" %%}' % app_relative_path
		return content == expected

	def test_no_theme_shadows_an_app_template(self):
		templates_root = os.path.join(APP_PATH, "templates")
		shadowed = []

		for theme_slug in os.listdir(THEMES_ROOT):
			theme_dir = os.path.join(THEMES_ROOT, theme_slug)
			if not os.path.isdir(theme_dir):
				continue
			for root, _dirs, files in os.walk(theme_dir):
				for filename in files:
					absolute_path = os.path.join(root, filename)
					relative_path = os.path.relpath(absolute_path, theme_dir)
					candidates = {relative_path}
					if relative_path.startswith("components" + os.sep):
						candidates.add(relative_path[len("components" + os.sep) :])
					for candidate in candidates:
						if not os.path.isfile(os.path.join(templates_root, candidate)):
							continue
						if self.is_one_line_passthrough(absolute_path, candidate):
							continue
						shadowed.append((theme_slug, relative_path))

		self.assertEqual(shadowed, [], f"Theme file(s) shadow an app template: {shadowed}")


class IntegrationTestThemeBaseContract(IntegrationTestCase):
	REQUIRED_BLOCKS = ("seo", "json_ld", "analytics_head", "analytics_events", "body", "head")

	def test_every_bundled_theme_base_defines_the_required_blocks(self):
		for theme_slug in os.listdir(THEMES_ROOT):
			base_path = os.path.join(THEMES_ROOT, theme_slug, "components", "base.html")
			if not os.path.isfile(base_path):
				continue
			with open(base_path) as base_file:
				source = base_file.read()
			for block_name in self.REQUIRED_BLOCKS:
				self.assertIsNotNone(
					re.search(r"\{%-?\s*block\s+" + block_name + r"\s*-?%\}", source),
					f"{theme_slug}/components/base.html is missing the required '{block_name}' block",
				)


class IntegrationTestThemedRendering(IntegrationTestCase):
	def setUp(self):
		self.settings = frappe.get_single("Shop Theme Settings")
		self.original_active_theme = self.settings.active_theme

	def tearDown(self):
		frappe.db.set_single_value("Shop Theme Settings", "active_theme", self.original_active_theme)
		frappe.clear_cache()

	def activate(self, theme_name):
		frappe.db.set_single_value("Shop Theme Settings", "active_theme", theme_name)
		frappe.clear_cache()

	def test_themed_and_unthemed_product_card_render_the_same_fields(self):
		from ls_shop.shop_themes.render import render_themed_template

		card_context = {
			"image": "/files/sample.jpg",
			"brand": "Sample",
			"product_name": "Sample Product",
			"formatted_price": 100.0,
			"original_price": 0,
			"discount": 0,
		}

		self.activate(None)
		unthemed_html = render_themed_template(
			'{% from "templates/macros/item_card.html" import item_card %}'
			"{{ item_card(image, brand, product_name, formatted_price, original_price, discount) }}",
			card_context,
		)

		self.activate("Shop Default Theme")
		themed_html = render_themed_template(
			'{% from "components/macros/product_card.html" import product_card %}'
			"{{ product_card(image, brand, product_name, formatted_price, original_price, discount) }}",
			card_context,
		)

		for expected in ("Sample Product", "sample.jpg"):
			self.assertIn(expected, unthemed_html)
			self.assertIn(expected, themed_html)

	def test_og_card_still_renders_with_no_active_theme(self):
		from ls_shop.shop_themes.render import render_themed_template

		self.activate(None)
		html = render_themed_template("<html><body>{{ label }}</body></html>", {"label": "card"})
		self.assertIn("card", html)

	def test_render_themed_template_falls_back_when_theme_has_no_dirs(self):
		from ls_shop.shop_themes.render import render_themed_template

		self.activate("Shop Default Theme")
		html = render_themed_template("<html><body>{{ label }}</body></html>", {"label": "card"})
		self.assertIn("card", html)
