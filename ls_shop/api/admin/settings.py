# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

EDITABLE_FIELDS = ("store_name", "contact_email", "contact_phone")


@frappe.whitelist()
def get_store_settings():
	"""The handful of Lifestyle Settings fields a store owner actually edits."""
	frappe.has_permission("Lifestyle Settings", ptype="read", throw=True)

	settings = frappe.get_cached_doc("Lifestyle Settings")
	return {field: settings.get(field) for field in EDITABLE_FIELDS}


@frappe.whitelist(methods=["POST"])
def save_store_settings(**kwargs):
	frappe.has_permission("Lifestyle Settings", ptype="write", throw=True)

	settings = frappe.get_doc("Lifestyle Settings")
	for field in EDITABLE_FIELDS:
		if field in kwargs:
			settings.set(field, kwargs[field])
	settings.save()

	return {field: settings.get(field) for field in EDITABLE_FIELDS}
