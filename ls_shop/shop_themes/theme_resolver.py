import importlib.util
import os

import frappe
from frappe.utils.jinja import get_jenv
from frappe.utils.jinja_globals import is_rtl
from frappe.website.doctype.website_settings.website_settings import get_website_settings
from frappe.website.utils import build_response
from jinja2 import BaseLoader, TemplateNotFound

from ls_shop.shop_themes.doctype.shop_theme.shop_theme import (
	get_render_theme_context,
	is_within_directory,
)
from ls_shop.shop_themes.doctype.shop_theme_settings.shop_theme_settings import get_compiled_routes

# page_renderer hooks are instantiated before every built-in renderer, so a first path
# segment missing from this set is a full route hijack rather than a 404.
RESERVED_PATH_SEGMENTS = frozenset(
	{
		"api",
		"app",
		"assets",
		"backups",
		"desk",
		"files",
		"login",
		"method",
		"og-image",
		"private",
		"robots.txt",
		"sitemap.xml",
		"llms.txt",
		"socket.io",
		"update-password",
		"website_script.js",
	}
)

# Every storefront route carries a language prefix, so a dynamic page can only ever live
# below one. This structurally excludes the root crawl infrastructure as well.
DYNAMIC_PAGE_LANG_PREFIXES = frozenset({"en", "ar"})

# A bare (non-theme://) template name is resolvable from a theme ONLY under this prefix.
# Anything else - notably every "templates/..." name - goes straight to the app loader, so a
# theme cannot shadow templates/includes/header.html and silently disconnect the menu
# manager and footer editor for the whole app.
THEME_OVERRIDABLE_PREFIX = "components/"

DEFAULT_APP_NAME = "Lifestyle"


def find_theme_file(theme_dirs, relative_path):
	for theme_dir in theme_dirs:
		candidate = os.path.join(theme_dir, relative_path)
		if is_within_directory(theme_dir, candidate) and os.path.isfile(candidate):
			return candidate
	return None


page_controller_modules = {}


def load_page_controller(theme_dirs, template_relative_path):
	controller_relative_path = f"{os.path.splitext(template_relative_path)[0]}.py"
	controller_path = find_theme_file(theme_dirs, controller_relative_path)
	if not controller_path:
		return None

	modified_time = os.path.getmtime(controller_path)
	cached = page_controller_modules.get(controller_path)
	if cached and cached[0] == modified_time:
		return cached[1]

	module_name = build_controller_module_name(theme_dirs, controller_path, controller_relative_path)
	spec = importlib.util.spec_from_file_location(module_name, controller_path)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	page_controller_modules[controller_path] = (modified_time, module)
	return module


def build_controller_module_name(theme_dirs, controller_path, relative_path):
	theme_slug = ""
	for theme_dir in theme_dirs:
		if os.path.join(theme_dir, relative_path) == controller_path:
			theme_slug = os.path.basename(theme_dir.rstrip(os.sep))
			break

	page_slug = os.path.splitext(relative_path)[0]
	for separator in (os.sep, "/", "-", "."):
		page_slug = page_slug.replace(separator, "_")

	return f"ls_shop.shop_themes.theme_pages.{theme_slug}.{page_slug}"


def run_page_controller(theme_dirs, template_relative_path, context):
	module = load_page_controller(theme_dirs, template_relative_path)
	if not module or not hasattr(module, "get_context"):
		return

	data = module.get_context(context)
	if data:
		context.update(data)


class ThemePageRenderer:
	def __init__(self, path, http_status_code=None):
		self.path = path
		self.http_status_code = http_status_code
		self.theme_dirs = None
		self.template_path = None
		self.match = None
		self.requires_auth = False

	def can_render(self):
		theme_context = get_render_theme_context()
		if not theme_context["theme_name"] or not theme_context["dirs"]:
			return False

		request_path = self.get_request_path()
		settings = get_compiled_routes()

		matched_route, match = match_route(settings["routes"], request_path)
		if matched_route:
			template_path = matched_route["template_path"]
			requires_auth = matched_route["requires_auth"]
		elif is_dynamic_page(settings, request_path):
			template_path = f"pages/{request_path}.html"
			requires_auth = False
		else:
			return False

		# Deliberately no fallback to a different template: an active theme that does not
		# ship this page declines, and stock frappe routing serves it untouched.
		if not find_theme_file(theme_context["dirs"], template_path):
			return False

		self.theme_dirs = theme_context["dirs"]
		self.template_path = template_path
		self.match = match
		self.requires_auth = requires_auth
		return True

	def get_request_path(self):
		# Matched against the RAW request path, not the endpoint website_route_rules rewrote
		# it to, so a themed route can bypass those rules.
		request = getattr(frappe.local, "request", None)
		if request:
			return request.path.strip("/")
		return self.path.strip("/")

	def render(self):
		if self.requires_auth and frappe.session.user == "Guest":
			raise frappe.PermissionError

		context = build_base_context(self.match)
		run_page_controller(self.theme_dirs, self.template_path, context)
		html = self.render_with_theme_loader(context)
		return build_response(self.path, html, self.http_status_code or 200)

	def render_with_theme_loader(self, context):
		jenv = get_jenv()
		theme_env = get_theme_environment(jenv, self.theme_dirs)
		template = theme_env.get_template(f"theme://{self.template_path}", globals=jenv.globals)
		return template.render(context)


def match_route(routes, request_path):
	for route in routes:
		match = route["pattern"].match(request_path)
		if match:
			return route, match
	return None, None


def is_dynamic_page(settings, request_path):
	if not settings["dynamic_pages_enabled"] or not request_path:
		return False

	first_segment = request_path.split("/")[0]
	if first_segment in RESERVED_PATH_SEGMENTS:
		return False

	# The allowlist is the real guard; the denylist above stays as the backstop for the day
	# a language prefix is added that collides with a core route.
	return first_segment in DYNAMIC_PAGE_LANG_PREFIXES


class ThemeFallbackLoader(BaseLoader):
	def __init__(self, theme_dirs, fallback_loader):
		self.theme_dirs = tuple(theme_dirs)
		self.fallback_loader = fallback_loader

	def get_source(self, environment, template):
		if template.startswith("theme://"):
			relative_path = template[len("theme://") :]
			full_path = find_theme_file(self.theme_dirs, relative_path)
			if full_path:
				return read_template_source(full_path)
			raise TemplateNotFound(template)

		if template.startswith(THEME_OVERRIDABLE_PREFIX):
			full_path = find_theme_file(self.theme_dirs, template)
			if full_path:
				return read_template_source(full_path)

		return self.fallback_loader.get_source(environment, template)


def read_template_source(full_path):
	modified_time = os.path.getmtime(full_path)
	# nosemgrep: frappe-semgrep-rules.rules.security.frappe-security-file-traversal
	with open(full_path) as source_file:
		source = source_file.read()
	return (
		source,
		full_path,
		lambda path=full_path, modified=modified_time: os.path.getmtime(path) == modified,
	)


theme_environments = {}


def get_theme_environment(jenv, theme_dirs):
	key = tuple(theme_dirs)
	theme_env = theme_environments.get(key)
	if theme_env is None:
		loader = ThemeFallbackLoader(theme_dirs, jenv.loader)
		theme_env = jenv.overlay(loader=loader)
		theme_env.auto_reload = bool(frappe.conf.get("developer_mode") or frappe._dev_server)
		theme_environments[key] = theme_env
	return theme_env


def build_base_context(match):
	context = frappe._dict(is_rtl=is_rtl(), csrf_token=frappe.sessions.get_csrf_token())

	if match:
		apply_route_groups(match, context)

	apply_website_settings(context)
	apply_website_context_hooks(context)

	return context


def apply_website_settings(context):
	context.app_name = DEFAULT_APP_NAME
	context.app_logo = None
	context.boot = {}

	try:
		# Also fills context.boot, so a themed page gets the same site-wide context
		# frappe's own renderers build. Never call get_boot_data() on top of this.
		context.update(get_website_settings())

		# get_website_settings() leaves out the branding fields a theme renders the brand
		# from, so a site never has to restate its own identity inside a theme.
		settings = frappe.client_cache.get_doc("Website Settings")
		context.app_name = settings.app_name or DEFAULT_APP_NAME
		context.app_logo = settings.app_logo
	except Exception:
		# Branding is cosmetic; a themed page must still render without it.
		frappe.log_error(title="Shop Theme: website settings failed")


def apply_route_groups(match, context):
	groups = match.groupdict() or {}
	if not groups:
		return

	# Merged into form_dict as well, so a www page controller written against
	# form_dict.get("route") keeps working when reused as a theme page controller.
	context.update(groups)
	frappe.local.form_dict.update(groups)


def apply_website_context_hooks(context):
	for hook_method in frappe.get_hooks("update_website_context"):
		values = frappe.get_attr(hook_method)(context)
		if values:
			context.update(values)
