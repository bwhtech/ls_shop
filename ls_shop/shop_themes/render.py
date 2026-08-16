import frappe
from frappe.utils.jinja import get_jenv, guess_is_path

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import get_theme_context, resolve_active_theme
from ls_shop.shop_themes.theme_resolver import get_theme_environment


def render_themed_template(template, context=None, theme_name=None):
	"""Render a template through the active theme's loader outside a request.

	OG cards, emails and background jobs run on the global jenv, which sees no theme
	overrides at all. Resolution here is from the settings only - never ?preview_theme,
	which needs a request - and falls back to frappe.render_template when no theme is
	active, so an unthemed site behaves exactly as before.

	`template` is a path or a template string, matching frappe.render_template.
	"""
	theme_context = get_theme_context(theme_name or resolve_active_theme())
	if not theme_context["dirs"]:
		return frappe.render_template(template, context)

	jenv = get_jenv()
	theme_env = get_theme_environment(jenv, theme_context["dirs"])

	if guess_is_path(template):
		compiled = theme_env.get_template(template, globals=jenv.globals)
	else:
		if ".__" in template:
			frappe.throw(frappe._("Illegal template"))
		compiled = theme_env.from_string(template, globals=jenv.globals)

	return compiled.render(context or {})
