# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""The three brand assets the storefront paints on every page: logo, footer logo, favicon.

Website Settings is the source of truth - it is what the store dashboard edits, and Frappe already
ships the fields. Lifestyle Settings' own three fields stay in the chain behind it as a legacy
fallback, so a site that branded itself before this module existed does not go blank on upgrade.
"""

import frappe
from frappe.utils.caching import request_cache

WEBSITE_SETTINGS = "Website Settings"
LEGACY_SETTINGS = "Lifestyle Settings"

BUNDLED_LOGO = "/assets/ls_shop/icons/lifestyle.svg"
BUNDLED_FOOTER_LOGO = "/assets/ls_shop/images/lifestyle.png"
BUNDLED_FAVICON = "/assets/ls_shop/images/meta/favicon-32x32.png"

# Website Settings labels `banner_image` "Brand Image" - that is the storefront's header logo.
BRAND_ASSET_FIELDS = {
	"logo": ("banner_image", "brand_logo"),
	"footer_logo": ("footer_logo", "footer_logo"),
	"favicon": ("favicon", "favicon"),
}


@request_cache
def get_configured_brand_assets() -> dict:
	"""Only what the shop owner actually set; each value is "" when neither doctype carries one.

	Callers that need something paintable want get_brand_assets() instead - this one exists for
	the places where "unset" has to stay distinguishable from "bundled default", such as the OG
	share image, where a 32px favicon is a worse answer than the share-image default.

	Cached per request rather than with site_cache (the idiom in bwh_payments.utils): site_cache
	lives in the worker process, so a save only clears the worker that took it and every other
	worker keeps serving the old logo until the TTL runs out - which a shop owner who just
	uploaded a logo reads as a broken save. Across requests the two get_cached_doc reads are the
	cache, and the framework already invalidates those on save; both docs are loaded by the
	website context of a storefront request anyway, so this adds no query to the page.
	"""
	website_settings = frappe.get_cached_doc(WEBSITE_SETTINGS)
	legacy_settings = frappe.get_cached_doc(LEGACY_SETTINGS)

	return {
		asset: website_settings.get(website_field) or legacy_settings.get(legacy_field) or ""
		for asset, (website_field, legacy_field) in BRAND_ASSET_FIELDS.items()
	}


def get_brand_assets():
	"""What a template paints: never empty, every asset falls through to a bundled default."""
	configured = get_configured_brand_assets()

	return frappe._dict(
		logo=configured["logo"] or BUNDLED_LOGO,
		# A shop that only ever uploaded one logo still wants it in the footer - the Pixio footer
		# cascaded that way before this module existed, and dropping it would blank those footers.
		footer_logo=configured["footer_logo"] or configured["logo"] or BUNDLED_FOOTER_LOGO,
		favicon=configured["favicon"] or BUNDLED_FAVICON,
	)
