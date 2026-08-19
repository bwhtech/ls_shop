# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	"""Gate the store admin SPA.

	Every endpoint under ls_shop/api/admin checks its own doctype permissions, but a visitor
	who cannot manage the catalog should never reach the shell at all - landing on an app that
	renders empty and errors on every call reads as broken rather than forbidden.
	"""
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/dashboard"
		raise frappe.Redirect

	if not frappe.has_permission("Item", ptype="write"):
		frappe.throw(_("You do not have access to the store dashboard."), frappe.PermissionError)

	context.no_cache = 1
