"""Jinja-exposed SEO fallbacks for pages whose controller sets no `context.seo`.

Controller methods are unreachable from the Jinja sandbox (`get_cached_doc` resolves to a
SafeDoc dict wrapper whose methods silently return None), so the storefront reaches the SEO
builders through these module-level methods registered in `hooks.jinja`.
"""

import frappe

from ls_shop import seo


def seo_page_meta():
	# A broken Lifestyle Settings doc must never 500 the storefront over meta tags.
	try:
		return seo.default_seo()
	except Exception:
		frappe.log_error(title="SEO default meta build failed")
		return {}


def seo_org_jsonld():
	try:
		return seo.org_website_json_ld()
	except Exception:
		frappe.log_error(title="SEO organization JSON-LD build failed")
		return []
