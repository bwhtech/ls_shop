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


PROFILE_FIELDS = ("first_name", "last_name", "user_image")


@frappe.whitelist()
def get_profile():
	"""The signed-in user's own profile. Always self-scoped - this is not user administration."""
	user = frappe.get_cached_doc("User", frappe.session.user)
	return {
		"name": user.name,
		"email": user.email,
		"full_name": user.full_name,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"user_image": user.user_image,
	}


@frappe.whitelist(methods=["POST"])
def save_profile(**kwargs):
	"""Edit your own profile only; changing anyone else's is User administration's job."""
	user = frappe.get_doc("User", frappe.session.user)
	for field in PROFILE_FIELDS:
		if field in kwargs:
			user.set(field, kwargs[field])
	user.save(ignore_permissions=True)

	return get_profile()
