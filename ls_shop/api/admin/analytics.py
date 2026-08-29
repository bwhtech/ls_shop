# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Read/write for Analytics Settings behind the dashboard's Analytics tab (System Manager only)."""

import frappe
from frappe.utils.data import cint, cstr

from ls_shop.api.admin.settings import coerce_field_value
from ls_shop.api.analytics_dashboard import is_provider_configured

ANALYTICS_SETTINGS_DOCTYPE = "Analytics Settings"

PLAIN_FIELDS = (
	"enable_first_party",
	"enable_ga4",
	"ga4_measurement_id",
	"ga4_property_id",
	"enable_facebook",
	"fb_pixel_id",
)

# Never leave the server. The client only ever learns whether each one holds a value.
SECRET_FIELDS = ("ga4_service_account_json", "fb_access_token")

SCRIPT_FIELDS = ("title", "enabled", "script")


def get_analytics_settings_doc():
	frappe.only_for("System Manager")
	return frappe.get_cached_doc(ANALYTICS_SETTINGS_DOCTYPE)


def format_custom_tracking_scripts(settings):
	return [
		{fieldname: row.get(fieldname) for fieldname in SCRIPT_FIELDS}
		for row in settings.custom_tracking_scripts
	]


@frappe.whitelist()
def get_analytics_settings():
	"""Everything the Analytics tab renders. Secrets are reported as set/not-set, never returned."""
	settings = get_analytics_settings_doc()

	data = {fieldname: settings.get(fieldname) for fieldname in PLAIN_FIELDS}
	for fieldname in SECRET_FIELDS:
		data[f"{fieldname}_is_set"] = bool(settings.get_password(fieldname, raise_exception=False))

	data["ga4_configured"] = is_provider_configured("ga4", settings)
	data["meta_configured"] = is_provider_configured("meta", settings)
	data["custom_tracking_scripts"] = format_custom_tracking_scripts(settings)
	return data


def apply_secret_values(settings, values, cleared_fieldnames):
	# A blank secret keeps the stored one: save_passwords() recognises Frappe's mask.
	for fieldname in SECRET_FIELDS:
		if fieldname in cleared_fieldnames:
			settings.set(fieldname, "")
			continue
		new_secret = cstr(values.get(fieldname) or "").strip()
		if new_secret:
			settings.set(fieldname, new_secret)


def apply_custom_tracking_scripts(settings, rows):
	settings.set("custom_tracking_scripts", [])
	for row in rows:
		title = cstr(row.get("title") or "").strip()
		script = cstr(row.get("script") or "").strip()
		if not title or not script:
			frappe.throw(frappe._("Every tracking script needs a title and a snippet"))
		settings.append(
			"custom_tracking_scripts",
			{"title": title, "enabled": cint(row.get("enabled")), "script": script},
		)


@frappe.whitelist(methods=["POST"])
def save_analytics_settings(**kwargs):
	frappe.only_for("System Manager")

	meta = frappe.get_meta(ANALYTICS_SETTINGS_DOCTYPE)
	settings = frappe.get_doc(ANALYTICS_SETTINGS_DOCTYPE)

	for fieldname in PLAIN_FIELDS:
		if fieldname not in kwargs:
			continue
		docfield = meta.get_field(fieldname)
		settings.set(fieldname, coerce_field_value(docfield.fieldtype, kwargs[fieldname]))

	cleared_fieldnames = set(frappe.parse_json(kwargs.get("cleared_secrets") or "[]"))
	unknown_secrets = cleared_fieldnames - set(SECRET_FIELDS)
	if unknown_secrets:
		frappe.throw(frappe._("Not an analytics secret: {0}").format(", ".join(sorted(unknown_secrets))))
	apply_secret_values(settings, kwargs, cleared_fieldnames)

	if "custom_tracking_scripts" in kwargs:
		apply_custom_tracking_scripts(settings, frappe.parse_json(kwargs["custom_tracking_scripts"]) or [])

	settings.save()
	frappe.clear_document_cache(ANALYTICS_SETTINGS_DOCTYPE)
	return get_analytics_settings()
