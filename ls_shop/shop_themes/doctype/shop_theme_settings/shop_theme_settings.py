import re

import frappe
from frappe.model.document import Document

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import clear_render_theme_context

LANG = r"(?P<lang>en|ar)"

# The routes the bundled themes ship pages for. Seeded from after_install AND after_migrate
# AND the patch: frappe writes every patch into the Patch Log as applied WITHOUT running it
# on a fresh install, and that log entry then blocks it from ever running, so a patch alone
# leaves new sites with no themed routes at all.
DEFAULT_ROUTES = [
	{"url_pattern": rf"^{LANG}$", "template_path": "pages/index.html", "requires_auth": 0},
	{
		"url_pattern": rf"^{LANG}/products$",
		"template_path": "pages/products/list.html",
		"requires_auth": 0,
	},
	{
		"url_pattern": rf"^{LANG}/products/(?P<route>.+)$",
		"template_path": "pages/products/details.html",
		"requires_auth": 0,
	},
	{"url_pattern": rf"^{LANG}/cart$", "template_path": "pages/cart/cart.html", "requires_auth": 0},
	# Gated by www.cart.checkout.get_context, not here. The resolver's own gate raises before any
	# controller runs, so a guest deep-linking to checkout got a bare 403 with no way back; the
	# controller sends them to the cart instead, where both themes offer the sign-in dialog.
	{
		"url_pattern": rf"^{LANG}/cart/checkout$",
		"template_path": "pages/cart/checkout.html",
		"requires_auth": 0,
	},
	{
		"url_pattern": rf"^{LANG}/account/dashboard$",
		"template_path": "pages/account/dashboard.html",
		"requires_auth": 1,
	},
	{
		"url_pattern": rf"^{LANG}/account/profile$",
		"template_path": "pages/account/profile.html",
		"requires_auth": 1,
	},
	{
		"url_pattern": rf"^{LANG}/account/orders$",
		"template_path": "pages/account/orders/index.html",
		"requires_auth": 1,
	},
	{
		"url_pattern": rf"^{LANG}/account/orders/detail$",
		"template_path": "pages/account/orders/detail.html",
		"requires_auth": 1,
	},
	# The only account route open to a logged-out shopper: it is the gateway return URL, so the money
	# is already taken by the time it loads. Refusing it outright leaves the shopper on a 403 with no
	# way back; the page asks for the login itself and shows nothing until it has one.
	{
		"url_pattern": rf"^{LANG}/account/orders/confirmation$",
		"template_path": "pages/account/orders/confirmation.html",
		"requires_auth": 0,
	},
	{
		"url_pattern": rf"^{LANG}/account/wishlist$",
		"template_path": "pages/account/wishlist.html",
		"requires_auth": 1,
	},
	{
		"url_pattern": rf"^{LANG}/account/address$",
		"template_path": "pages/account/address.html",
		"requires_auth": 1,
	},
]

COMPILED_ROUTES_CACHE_KEY = "shop_theme_compiled_routes"


class ShopThemeSettings(Document):
	def validate(self):
		for row in self.get("routes") or []:
			try:
				re.compile(row.url_pattern)
			except re.error as error:
				frappe.throw(frappe._("Invalid regex in route {0}: {1}").format(row.url_pattern, error))

	def on_update(self):
		clear_settings_cache()


def seed_default_routes():
	"""Add any missing default route. Idempotent on url_pattern, so custom routes survive
	and dynamic_pages_enabled is never re-enabled behind an admin's back."""
	settings = frappe.get_single("Shop Theme Settings")
	existing_patterns = {row.url_pattern for row in settings.routes}

	missing_routes = [route for route in DEFAULT_ROUTES if route["url_pattern"] not in existing_patterns]
	if not missing_routes:
		return

	for route in missing_routes:
		settings.append("routes", route)

	settings.save(ignore_permissions=True)


def clear_settings_cache():
	frappe.cache.delete_value(COMPILED_ROUTES_CACHE_KEY)
	frappe.local.shop_theme_compiled_routes = None
	# The active theme lives on this Single, so the memoised render context is stale too.
	clear_render_theme_context()


def build_compiled_routes():
	settings = frappe.get_cached_doc("Shop Theme Settings")
	compiled = []
	for row in settings.get("routes") or []:
		try:
			pattern = re.compile(row.url_pattern)
		except re.error:
			continue
		compiled.append(
			{
				"pattern": pattern,
				"template_path": row.template_path,
				"requires_auth": bool(row.requires_auth),
			}
		)
	return {"routes": compiled, "dynamic_pages_enabled": bool(settings.dynamic_pages_enabled)}


def get_compiled_routes():
	# Memoised on frappe.local over redis as well: regex compilation showed up hot when
	# every request re-read the table.
	routes = getattr(frappe.local, "shop_theme_compiled_routes", None)
	if routes is None:
		routes = frappe.cache.get_value(COMPILED_ROUTES_CACHE_KEY, generator=build_compiled_routes)
		frappe.local.shop_theme_compiled_routes = routes
	return routes
