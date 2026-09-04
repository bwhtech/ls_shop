# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from ls_shop.shop_themes.render import render_themed_template
from ls_shop.shop_themes.theme_resolver import find_theme_file

PREVIEW_LAYOUTS = ("components/theme_layout.html", "components/base.html")

# The seo/analytics blocks are blanked because they would emit tracking from inside an editor pane.
COMMON_BLANKED_BLOCKS = (
	"seo",
	"json_ld",
	"analytics_head",
	"analytics_events",
	"body",
	"uncontained_body",
)

# Both naming conventions: the base theme uses `header`/`footer`, Pixio `site_header`/`site_footer`.
# Not chrome_top/chrome_bottom: Pixio opens .page-wraper in one and closes it in the other.
HEADER_BLOCKS = ("header", "site_header")
FOOTER_BLOCKS = ("footer", "site_footer")


def get_preview_layout(theme_context):
	"""The active theme's layout, most specific first, or None when no theme is active."""
	return next(
		(
			candidate
			for candidate in PREVIEW_LAYOUTS
			if theme_context["dirs"] and find_theme_file(theme_context["dirs"], candidate)
		),
		None,
	)


def get_preview_template(layout, blanked_blocks):
	blanks = "".join(f"{{% block {name} %}}{{% endblock %}}" for name in blanked_blocks)
	# super() keeps the theme's own head - its stylesheets - and appends the previewed colours.
	head = "{% block head %}{{ super() }}{{ preview_theme_css }}{% endblock %}"
	return f'{{% extends "{layout}" %}}{blanks}{head}'


def render_chrome_preview(context, blanked_blocks):
	"""Render the active theme's layout with `blanked_blocks` emptied, or None if no theme is active."""
	theme_name = resolve_active_theme()
	theme_context = get_theme_context(theme_name)
	layout = get_preview_layout(theme_context)
	if not layout:
		return None

	return render_themed_template(
		get_preview_template(layout, blanked_blocks), context, theme_name=theme_name
	)


def get_preview_context(preview_settings, lang):
	"""The context every chrome preview needs, whichever end of the page it is rendering."""
	# base.html reads the page language off frappe.lang, so the ?lang switch must move it here.
	frappe.local.lang = lang

	return frappe._dict(
		preview_settings=preview_settings,
		lang=lang,
		is_rtl=lang == "ar",
		# format_theme_css() in the layout reads the SAVED doc, so this live copy is appended after to win.
		preview_theme_css=preview_settings.generate_theme_css(),
		# The default theme's base renders a breadcrumb outside any block, guarded only by this.
		show_breadcrumb=False,
	)
