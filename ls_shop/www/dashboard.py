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

	# The page template writes every key of `boot` onto `window`, which is where frappe-ui's
	# fetch layer reads the CSRF token from. Without it the app still renders and every read
	# still works - only writes fail, because GET is not CSRF-checked and POST is.
	# `get_csrf_token` issues the token into the session, so it has to be committed to outlive
	# this request.
	context.boot = frappe._dict({"csrf_token": frappe.sessions.get_csrf_token()})
	frappe.db.commit()  # nosemgrep: frappe-semgrep-rules.rules.frappe-manual-commit

	context.no_cache = 1
