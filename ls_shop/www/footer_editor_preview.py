# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Renders the storefront footer with the *unsaved* Desk form values so the footer editor's iframe
shows what the shop owner is typing before they hit save."""

import re

import frappe
from frappe.utils import cstr, escape_html, validate_url

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.editor_input import SAFE_URL_SCHEMES
from ls_shop.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from ls_shop.shop_themes.render import render_themed_template
from ls_shop.shop_themes.theme_resolver import find_theme_file

# The preview renders through the active theme's own layout, most specific first, rather than
# rendering the footer partial on a hand-built page. A theme declares its stylesheets inside the
# layout's `head` block - Pixio links six of them - so any head assembled here is a second copy that
# drifts the moment a theme adds a file. Extending the layout also inherits its `body_class`, its
# `dir`, and format_theme_css(), which is what makes the preview match the storefront.
PREVIEW_LAYOUTS = ("components/theme_layout.html", "components/base.html")
BASE_FOOTER = "templates/includes/footer.html"

# Everything that is not the footer. Blanked rather than left to render, because the preview is a
# footer preview - and because seo/analytics blocks would emit tracking from inside an editor pane.
# Blanking chrome_top instead would unbalance the layout: Pixio opens .page-wraper there and closes
# it in chrome_bottom alongside the footer, so the footer would render outside the wrapper every rule
# in the theme scopes under. The header lives in its own block in both themes - `header` in the
# default theme's base, `site_header` in Pixio's layout - so those come out and the wrapper stays.
BLANKED_BLOCKS = (
	"seo",
	"json_ld",
	"analytics_head",
	"analytics_events",
	"header",
	"site_header",
	"body",
	"uncontained_body",
)

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

	footer_context = frappe._dict(
		preview_settings=settings,
		lang=lang,
		is_rtl=lang == "ar",
		# The layout emits format_theme_css(), which reads the SAVED doc - it cannot see the colour
		# the owner is dragging right now. This is the same CSS generated off the previewed doc, and
		# it is appended after the layout's own so it wins.
		preview_theme_css=settings.generate_theme_css(),
		# The default theme's base renders a breadcrumb outside any block, guarded only by this.
		show_breadcrumb=False,
	)

	# base.html reads the page language off frappe.lang, so the ?lang switch has to move it here
	# rather than only reaching the footer partial through the context.
	frappe.local.lang = lang

	theme_name = resolve_active_theme()
	theme_context = get_theme_context(theme_name)
	layout = next(
		(
			candidate
			for candidate in PREVIEW_LAYOUTS
			if theme_context["dirs"] and find_theme_file(theme_context["dirs"], candidate)
		),
		None,
	)
	if layout:
		context.rendered_html = render_themed_template(
			get_preview_template(layout), footer_context, theme_name=theme_name
		)
		return

	context.rendered_html = f"""<!DOCTYPE html>
<html lang="{escape_html(lang)}" dir="{"rtl" if footer_context.is_rtl else "ltr"}">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="/assets/ls_shop/css/tailwind.css">
{settings.generate_theme_css()}
</head>
<body>
{frappe.render_template(BASE_FOOTER, footer_context)}
</body>
</html>"""


def get_preview_template(layout):
	blanks = "".join(f"{{% block {name} %}}{{% endblock %}}" for name in BLANKED_BLOCKS)
	# super() keeps the theme's own head - its stylesheets - and appends the previewed colours.
	head = "{% block head %}{{ super() }}{{ preview_theme_css }}{% endblock %}"
	return f'{{% extends "{layout}" %}}{blanks}{head}'
