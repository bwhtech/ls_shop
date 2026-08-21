# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Renders one piece of the storefront's chrome - the header or the footer - on its own.

Shared by the footer editor and the navigation editor, which want the same thing pointed at opposite
ends of the page. Rendering runs THROUGH the active theme's own layout with every other block blanked,
never by dropping the partial onto a hand-built page: a theme declares its stylesheets inside the
layout's `head` block (Pixio links six), so any head assembled here is a second copy that drifts the
moment a theme adds a file. Extending the layout also inherits `body_class`, `dir` and the merchant's
theme CSS, which is what makes a preview match the storefront instead of merely resembling it.
"""

import frappe

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from ls_shop.shop_themes.render import render_themed_template
from ls_shop.shop_themes.theme_resolver import find_theme_file

PREVIEW_LAYOUTS = ("components/theme_layout.html", "components/base.html")

# Never part of a chrome preview: page content, and the seo/analytics blocks, which would otherwise
# emit tracking from inside an editor pane.
COMMON_BLANKED_BLOCKS = (
	"seo",
	"json_ld",
	"analytics_head",
	"analytics_events",
	"body",
	"uncontained_body",
)

# Each end of the page, under both naming conventions. The default theme's base calls them `header`
# and `footer`; Pixio names its own markup `site_header`/`site_footer`, reserving the plain names for
# the one-line passthroughs to the base templates.
#
# These are the blocks to blank, and they are deliberately NOT `chrome_top`/`chrome_bottom`: Pixio
# opens .page-wraper in chrome_top and closes it in chrome_bottom, so blanking either one leaves the
# surviving half of the page outside the element every theme rule is scoped under.
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
	# base.html reads the page language off frappe.lang, so the ?lang switch has to move it here
	# rather than only reaching the partial through the context.
	frappe.local.lang = lang

	return frappe._dict(
		preview_settings=preview_settings,
		lang=lang,
		is_rtl=lang == "ar",
		# The layout emits format_theme_css(), which reads the SAVED doc - it cannot see the colour
		# the owner is dragging right now. This is the same CSS generated off the previewed doc, and
		# it is appended after the layout's own so it wins.
		preview_theme_css=preview_settings.generate_theme_css(),
		# The default theme's base renders a breadcrumb outside any block, guarded only by this.
		show_breadcrumb=False,
	)
