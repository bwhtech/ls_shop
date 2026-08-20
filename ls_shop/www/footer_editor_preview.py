# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Renders the storefront footer with the *unsaved* Desk form values so the footer editor's iframe
shows what the shop owner is typing before they hit save."""

import re

import frappe
from frappe.utils import cstr, escape_html, validate_url

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.editor_input import SAFE_URL_SCHEMES
from ls_shop.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from ls_shop.shop_themes.jinja_helpers import shop_theme_asset_url
from ls_shop.shop_themes.render import render_themed_template
from ls_shop.shop_themes.theme_resolver import find_theme_file
from ls_shop.utils import format_theme_css

# What a themed page includes. A theme that ships its own footer is the one the shopper sees, so
# previewing the base template instead would show markup the storefront never renders.
THEMED_FOOTER = "components/includes/footer.html"
BASE_FOOTER = "templates/includes/footer.html"

no_cache = True

PREVIEW_OVERRIDE_FIELDS = (
	"newsletter_title",
	"newsletter_description",
	"copyright_text",
	"contact_phone",
	"contact_email",
	"working_hours",
	"store_name",
	"footer_logo",
	"payment_methods_image",
	"vat_certificate_image",
	"facebook_url",
	"instagram_url",
	"twitter_url",
	"tiktok_url",
	"snapchat_url",
	"footer_bg_color",
	"footer_text_color",
)

# These land inside the <style> block generate_theme_css() builds, where escaping is no defence —
# only an exact hex match keeps `#fff};x:expression(1)` out of the stylesheet.
COLOR_FIELDS = ("footer_bg_color", "footer_text_color")
COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3}([0-9a-fA-F]{2})?)?$")

# These land in an href/src attribute, so escaping is not enough either — javascript: and data:
# survive escaping intact.
URL_FIELDS = (
	"footer_logo",
	"payment_methods_image",
	"vat_certificate_image",
	"facebook_url",
	"instagram_url",
	"twitter_url",
	"tiktok_url",
	"snapchat_url",
)

PREVIEW_LANGUAGES = ("en", "ar")


def get_context(context):
	frappe.has_permission("Lifestyle Settings", "write", throw=True)

	settings = frappe.get_single("Lifestyle Settings")
	for fieldname in PREVIEW_OVERRIDE_FIELDS:
		value = frappe.form_dict.get(fieldname)
		# Werkzeug hands back a list when a param repeats.
		if isinstance(value, list | tuple):
			value = value[0] if value else None
		value = cstr(value) if value is not None else ""
		if not value:
			continue

		if fieldname in COLOR_FIELDS:
			if not COLOR_PATTERN.match(value):
				continue
		else:
			if fieldname in URL_FIELDS and not validate_url(value, valid_schemes=SAFE_URL_SCHEMES):
				continue
			value = escape_html(value)

		setattr(settings, fieldname, value)

	lang = frappe.form_dict.get("lang")
	if lang not in PREVIEW_LANGUAGES:
		lang = frappe.local.lang or "en"

	footer_context = frappe._dict(preview_settings=settings, lang=lang, is_rtl=lang == "ar")

	theme_context = get_theme_context(resolve_active_theme())
	if theme_context["dirs"] and find_theme_file(theme_context["dirs"], THEMED_FOOTER):
		footer_html = render_themed_template(THEMED_FOOTER, footer_context)
		# The theme's own stylesheet, the way its base.html loads it - without this the theme's
		# markup renders against base tailwind alone and looks nothing like the storefront.
		theme_styles = (
			f'<link rel="stylesheet" href="{escape_html(shop_theme_asset_url("tailwind.output.css"))}">'
			f"{format_theme_css()}"
		)
	else:
		footer_html = frappe.render_template(BASE_FOOTER, footer_context)
		theme_styles = ""

	context.rendered_html = f"""<!DOCTYPE html>
<html lang="{escape_html(lang)}">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="/assets/ls_shop/css/tailwind.css">
{theme_styles}
{settings.generate_theme_css()}
</head>
<body>
{footer_html}
</body>
</html>"""
