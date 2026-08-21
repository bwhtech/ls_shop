# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe

from ls_shop.branding import BRAND_ASSET_FIELDS, LEGACY_SETTINGS, WEBSITE_SETTINGS


def execute():
	"""Seed Website Settings from the legacy Lifestyle Settings branding fields.

	The store dashboard edits Website Settings, so it has to open showing whatever the storefront
	is already serving. A Website Settings value that is already set is the newer of the two and
	is left alone, which is also what makes a second run a no-op.
	"""
	legacy_settings = frappe.get_cached_doc(LEGACY_SETTINGS)
	website_settings = frappe.get_doc(WEBSITE_SETTINGS)

	copied_fields = []
	for website_field, legacy_field in BRAND_ASSET_FIELDS.values():
		legacy_value = legacy_settings.get(legacy_field)
		if not legacy_value or website_settings.get(website_field):
			continue
		website_settings.set(website_field, legacy_value)
		copied_fields.append(website_field)

	if not copied_fields:
		return

	website_settings.save()
	print(f"Copied brand assets to Website Settings: {', '.join(copied_fields)}")
