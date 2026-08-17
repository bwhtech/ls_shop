import os

import frappe

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import (
	get_render_theme_context,
	is_within_directory,
)


def shop_theme_asset_url(path):
	"""Resolve a public asset against the theme inheritance chain, child first.

	Names are app-prefixed because jinja hook methods share one global dict keyed by
	function name and the last app registered wins - an unprefixed collision shows up as
	empty asset URLs, not as an error.
	"""
	theme_context = get_render_theme_context()
	if not theme_context["theme_name"]:
		return ""

	relative_path = path.lstrip("/")
	apps = theme_context["apps"]

	for name in theme_context["names"]:
		app = apps[name]
		slug = frappe.scrub(name)
		theme_public_dir = os.path.join(frappe.get_app_path(app), "public", "themes", slug)
		asset_path = os.path.join(theme_public_dir, relative_path)
		if is_within_directory(theme_public_dir, asset_path) and os.path.isfile(asset_path):
			return f"/assets/{app}/themes/{slug}/{relative_path}"

	# No theme in the chain ships the file. Fall back to the ACTIVE theme's URL, not the
	# root ancestor's, so a missing asset reads as this theme's broken URL.
	active_name = theme_context["names"][0]
	active_app = apps[active_name]
	return f"/assets/{active_app}/themes/{frappe.scrub(active_name)}/{relative_path}"


def shop_theme_config():
	"""The active theme's settings Single, for reading FIELDS off in a template.

	Never call a controller method on the returned document from a template: frappe's jinja
	sandbox hands templates a SafeDoc dict wrapper where methods silently resolve to None.
	"""
	theme_context = get_render_theme_context()
	settings_doctype = theme_context.get("settings_doctype")
	if not settings_doctype:
		return frappe._dict()

	return frappe.get_cached_doc(settings_doctype)
