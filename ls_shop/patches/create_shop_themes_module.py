import frappe

MODULE_NAME = "Shop Themes"


def execute():
	"""Create the Module Def the Shop Themes doctypes are filed under.

	frappe's add_module_defs() runs only at install, so on an already-installed site the
	new modules.txt line does nothing and sync_for() silently skips every doctype in it.
	Runs pre-model-sync because DocType.module is a Link that must already resolve.
	"""
	if not frappe.db.exists("Module Def", MODULE_NAME):
		module_def = frappe.new_doc("Module Def")
		module_def.module_name = MODULE_NAME
		module_def.app_name = "ls_shop"
		module_def.custom = 0
		module_def.insert(ignore_permissions=True)

	# frappe.local.app_modules is a redis-cached read of modules.txt taken when this process
	# booted, and sync_for() walks exactly that list. Without refreshing it the new module is
	# skipped and its doctypes are silently not created until a second migrate.
	frappe.cache.delete_value("app_modules")
	frappe.client_cache.delete_value("installed_app_modules")
	frappe.setup_module_map()
