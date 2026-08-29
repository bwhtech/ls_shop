# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/dashboard"
		raise frappe.Redirect

	if not frappe.has_permission("Item", ptype="write"):
		frappe.throw(_("You do not have access to the store dashboard."), frappe.PermissionError)

	# get_csrf_token issues the token into the session, so it must be committed to outlive this request.
	context.boot = frappe._dict({"csrf_token": frappe.sessions.get_csrf_token()})
	frappe.db.commit()  # nosemgrep: frappe-semgrep-rules.rules.frappe-manual-commit

	context.no_cache = 1
