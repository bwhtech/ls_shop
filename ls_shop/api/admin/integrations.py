# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Provider-agnostic engine behind every integration screen on the dashboard.

Nothing here knows what a payment is. A caller supplies a registry entry and gets the read and the
write for free, so `bwh_shipping` adds its screen with a second registry plus two whitelisted wrappers:

	{
		"slug": "razorpay",                                # stable id the dashboard writes back
		"label": "Razorpay",                               # profile name, and the shopper-facing name
		"blurb": "Cards, UPI, netbanking and wallets.",
		"settings_doctype": "Razorpay Gateway Settings",   # the Single holding credentials
		"docs_url": "https://...",
		"profile_doctype": "Payment Gateway Profile",      # registry row the integration owns
		"profile_settings_fieldname": "gateway_settings",  # its Link back to the Single
		"webhook_path": "/api/method/...?gateway={profile}",  # optional
		"on_enable": callable(integration) | None,         # side setup an enabled provider needs
	}
"""

import frappe
from frappe.utils import get_url
from frappe.utils.data import cint

from ls_shop.api.admin.settings import coerce_field_value

# Layout-only, action-only, and child-table fieldtypes the generic renderer cannot express as a
# single input.
SKIPPED_FIELDTYPES = frozenset({"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Table"})

# The card's own toggle owns this field, so offering it inside a group would render two controls
# that fight over the same value.
ENABLED_FIELDNAME = "enabled"

# The fields a provider declares before its first Section Break. They are behaviour flags as often
# as credentials, so the fallback label has to stay neutral - calling it "Credentials" put Razorpay's
# Test Mode switch under a heading that promised API keys.
DEFAULT_GROUP_LABEL = "General"


def is_available(integration) -> bool:
	"""Whether the provider's app is installed on this site.

	A registry entry outlives the app that backs it - bwh_payments can be uninstalled, or a gateway
	dropped - and the dashboard has to keep rendering the other cards instead of erroring.
	"""
	return bool(frappe.db.exists("DocType", integration["settings_doctype"]))


def get_editable_docfields(settings_doctype):
	"""Every docfield a store owner may fill in, in Desk layout order, tagged with its group label."""
	docfields = []
	group_label = DEFAULT_GROUP_LABEL

	for docfield in frappe.get_meta(settings_doctype).fields:
		if docfield.fieldtype == "Section Break":
			group_label = docfield.label or DEFAULT_GROUP_LABEL
			continue
		if docfield.fieldtype in SKIPPED_FIELDTYPES:
			continue
		if docfield.hidden or docfield.read_only or docfield.fieldname == ENABLED_FIELDNAME:
			continue

		docfields.append((group_label, docfield))

	return docfields


def build_field_groups(settings_doctype, settings):
	"""The settings Single rendered as groups of fields, one group per Section Break."""
	groups = []
	group_by_label = {}

	for group_label, docfield in get_editable_docfields(settings_doctype):
		group = group_by_label.get(group_label)
		if group is None:
			group = {"label": group_label, "fields": []}
			group_by_label[group_label] = group
			groups.append(group)

		group["fields"].append(build_field(docfield, settings))

	return groups


def build_field(docfield, settings):
	"""One docfield as the dashboard sees it. A secret reports whether it is stored, never what it is."""
	stored_value = settings.get(docfield.fieldname)
	is_secret = docfield.fieldtype == "Password"

	return {
		"fieldname": docfield.fieldname,
		"label": docfield.label,
		"fieldtype": docfield.fieldtype,
		"options": docfield.options,
		"description": docfield.description,
		"required": bool(docfield.reqd),
		"value": None if is_secret else stored_value,
		"is_secret": is_secret,
		"is_set": stored_value not in (None, ""),
	}


def get_missing_fields(settings_doctype, settings):
	"""Required fieldnames still blank on the settings Single."""
	return [
		docfield.fieldname
		for _group_label, docfield in get_editable_docfields(settings_doctype)
		if docfield.reqd and settings.get(docfield.fieldname) in (None, "")
	]


def get_webhook_url(integration):
	webhook_path = integration.get("webhook_path")
	if not webhook_path:
		return None

	return get_url(webhook_path.format(profile=integration["label"]))


def is_profile_enabled(integration) -> bool:
	profile_doctype = integration["profile_doctype"]
	if not frappe.db.exists("DocType", profile_doctype):
		return False

	return bool(frappe.db.get_value(profile_doctype, integration["label"], ENABLED_FIELDNAME))


def describe_integration(integration):
	"""One integration card: what it is, whether it is live, and the fields behind its dialog."""
	settings_doctype = integration["settings_doctype"]
	description = {
		"slug": integration["slug"],
		"label": integration["label"],
		"blurb": integration.get("blurb"),
		"settings_doctype": settings_doctype,
		"available": is_available(integration),
		"enabled": False,
		"configured": False,
		"missing": [],
		"webhook_url": None,
		"docs_url": integration.get("docs_url"),
		"groups": [],
	}
	if not description["available"]:
		return description

	frappe.has_permission(settings_doctype, ptype="read", throw=True)

	settings = frappe.get_cached_doc(settings_doctype)
	missing = get_missing_fields(settings_doctype, settings)
	description.update(
		{
			"enabled": is_profile_enabled(integration),
			"configured": not missing,
			"missing": missing,
			"webhook_url": get_webhook_url(integration),
			"groups": build_field_groups(settings_doctype, settings),
		}
	)
	return description


def write_settings(integration, values):
	"""Apply the submitted values to the settings Single and hand the unsaved doc back."""
	settings_doctype = integration["settings_doctype"]
	docfield_by_fieldname = {
		docfield.fieldname: docfield for _group_label, docfield in get_editable_docfields(settings_doctype)
	}

	unknown_fieldnames = set(values) - set(docfield_by_fieldname)
	if unknown_fieldnames:
		frappe.throw(
			frappe._("{0} has no field {1}").format(settings_doctype, ", ".join(sorted(unknown_fieldnames)))
		)

	settings = frappe.get_doc(settings_doctype)
	for fieldname, docfield in docfield_by_fieldname.items():
		if fieldname not in values:
			continue

		value = values[fieldname]
		# The dashboard never receives a stored secret, so it submits an empty box for one it did not
		# touch. Only an explicit null - a deliberate "clear this" - may wipe what is stored.
		if docfield.fieldtype == "Password" and value == "":
			continue

		settings.set(fieldname, coerce_field_value(docfield.fieldtype, value))

	return settings


def save_profile(integration, enabled):
	"""Upsert the registry row that makes the provider visible to the rest of the app.

	Saved as a Document rather than db_set so the profile's own hooks run - they are what clear the
	site cache the storefront reads its available providers from.
	"""
	profile_doctype = integration["profile_doctype"]
	label = integration["label"]

	if frappe.db.exists(profile_doctype, label):
		profile = frappe.get_doc(profile_doctype, label)
	elif not enabled:
		return
	else:
		profile = frappe.new_doc(profile_doctype)
		profile.name = label

	profile.set(integration["profile_settings_fieldname"], integration["settings_doctype"])
	profile.enabled = enabled
	profile.save()


def save_integration(integration, enabled, values):
	"""Write credentials, then flip the provider on or off. Returns the refreshed card."""
	settings_doctype = integration["settings_doctype"]
	if not is_available(integration):
		frappe.throw(frappe._("{0} is not installed on this site").format(settings_doctype))

	frappe.has_permission(settings_doctype, ptype="write", throw=True)

	enabled = cint(enabled)
	settings = write_settings(integration, values)

	if enabled:
		missing = get_missing_fields(settings_doctype, settings)
		if missing:
			frappe.throw(
				frappe._("Fill in {0} before enabling {1}").format(
					", ".join(
						frappe.get_meta(settings_doctype).get_label(fieldname) for fieldname in missing
					),
					integration["label"],
				)
			)

	if settings.meta.has_field(ENABLED_FIELDNAME):
		settings.set(ENABLED_FIELDNAME, enabled)
	settings.save()

	save_profile(integration, enabled)

	on_enable = integration.get("on_enable")
	if enabled and on_enable:
		on_enable(integration)

	return describe_integration(integration)
