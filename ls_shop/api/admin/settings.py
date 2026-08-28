# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.data import cint, cstr, flt

SETTINGS_DOCTYPE = "Lifestyle Settings"
BRANDING_DOCTYPE = "Website Settings"

# The Store tab spans two doctypes: the three brand assets moved to Website Settings, which is where
# Frappe already keeps them and where ls_shop.branding reads them from; everything else on the tab
# stays on Lifestyle Settings. The payload keys below are the pre-move ones on purpose - the Vue tab
# and the sidebar bind to them - so this map is the only place the two names meet.
BRANDING_FIELDS = {
	"brand_logo": "banner_image",
	"footer_logo": "footer_logo",
	"favicon": "favicon",
}

STORE_DETAIL_FIELDS = (
	"store_name",
	"brand_logo",
	"footer_logo",
	"favicon",
	"contact_email",
	"contact_phone",
	"working_hours",
	"company",
)

STORE_DETAIL_SETTINGS_FIELDS = tuple(
	fieldname for fieldname in STORE_DETAIL_FIELDS if fieldname not in BRANDING_FIELDS
)

SHIPPING_FIELDS = ("shipping_rule", "return_period")

PAYMENT_FIELDS = (
	"cod_enabled",
	"cod_charge",
	"cod_charge_applicable_below",
	"charge_account_head",
)

FOOTER_FIELDS = (
	"facebook_url",
	"twitter_url",
	"instagram_url",
	"snapchat_url",
	"tiktok_url",
	"newsletter_title",
	"newsletter_description",
	"copyright_text",
	"payment_methods_image",
	"vat_certificate_image",
)

# Everything the four hand-shaped tabs already own, so the generic Advanced tab does not
# render a second copy of the same control.
CURATED_FIELDS = frozenset(STORE_DETAIL_FIELDS + SHIPPING_FIELDS + PAYMENT_FIELDS + FOOTER_FIELDS)

# Layout-only, action-only, or child-table fieldtypes the generic renderer cannot express as
# a single input. Color is skipped for a different reason: the storefront is moving to
# theme-owned colour, so these fields are on their way out - format_theme_css() still reads
# them and must keep working, but offering them here would invite edits to a mechanism being
# replaced.
ADVANCED_SKIPPED_FIELDTYPES = frozenset(
	{"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Table", "Color"}
)

NUMERIC_FIELDTYPES = frozenset({"Currency", "Float", "Percent"})
INTEGER_FIELDTYPES = frozenset({"Int", "Check"})


def read_settings_fields(fieldnames):
	"""Read a fixed set of Lifestyle Settings fields for a settings tab."""
	frappe.has_permission(SETTINGS_DOCTYPE, ptype="read", throw=True)

	settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
	return {fieldname: settings.get(fieldname) for fieldname in fieldnames}


def coerce_field_value(fieldtype, value):
	"""Cast an incoming form value to what the docfield expects."""
	if value is None:
		return None
	if fieldtype in INTEGER_FIELDTYPES:
		return cint(value)
	if fieldtype in NUMERIC_FIELDTYPES:
		return flt(value)
	return cstr(value)


def write_settings_fields(allowed_fieldnames, values):
	"""Write only the whitelisted fields, casting each by its docfield type."""
	frappe.has_permission(SETTINGS_DOCTYPE, ptype="write", throw=True)

	meta = frappe.get_meta(SETTINGS_DOCTYPE)
	settings = frappe.get_doc(SETTINGS_DOCTYPE)
	for fieldname in allowed_fieldnames:
		if fieldname not in values:
			continue
		docfield = meta.get_field(fieldname)
		if not docfield:
			frappe.throw(frappe._("Unknown setting {0}").format(fieldname))
		settings.set(fieldname, coerce_field_value(docfield.fieldtype, values[fieldname]))

	settings.save()
	return {fieldname: settings.get(fieldname) for fieldname in allowed_fieldnames}


def read_branding_fields():
	"""The three brand assets, off Website Settings, under the payload's own key names."""
	frappe.has_permission(BRANDING_DOCTYPE, ptype="read", throw=True)

	website_settings = frappe.get_cached_doc(BRANDING_DOCTYPE)
	return {key: website_settings.get(fieldname) for key, fieldname in BRANDING_FIELDS.items()}


def write_branding_fields(values):
	"""Write whichever brand assets the payload carries. Website Settings gets its own permission
	check - a role that may edit Lifestyle Settings is not thereby allowed to edit the website."""
	if not any(key in values for key in BRANDING_FIELDS):
		return read_branding_fields()

	frappe.has_permission(BRANDING_DOCTYPE, ptype="write", throw=True)

	meta = frappe.get_meta(BRANDING_DOCTYPE)
	website_settings = frappe.get_doc(BRANDING_DOCTYPE)
	for key, fieldname in BRANDING_FIELDS.items():
		if key in values:
			fieldtype = meta.get_field(fieldname).fieldtype
			website_settings.set(fieldname, coerce_field_value(fieldtype, values[key]))

	website_settings.save()
	return {key: website_settings.get(fieldname) for key, fieldname in BRANDING_FIELDS.items()}


def validate_store_details(values):
	"""Guard the one store detail the docfield cannot guard for us.

	The rest of the tab is already covered by the framework: `company` is a mandatory docfield and
	`contact_email` carries options="Email", so a blank or malformed value fails inside save().
	`store_name` is neither, yet ls_shop.seo falls back to the literal "Store" when it is empty -
	so an empty save silently rebrands every storefront <title> and JSON-LD name.
	"""
	if "store_name" in values and not cstr(values["store_name"]).strip():
		frappe.throw(frappe._("Store Name is required"), frappe.MandatoryError)


@frappe.whitelist()
def get_store_settings():
	"""Branding and contact details - the fields a store owner touches most."""
	return read_settings_fields(STORE_DETAIL_SETTINGS_FIELDS) | read_branding_fields()


@frappe.whitelist(methods=["POST"])
def save_store_settings(**kwargs):
	validate_store_details(kwargs)
	return write_settings_fields(STORE_DETAIL_SETTINGS_FIELDS, kwargs) | write_branding_fields(kwargs)


@frappe.whitelist()
def get_shipping_settings():
	"""Shipping rule and returns window, plus the return reasons for reference."""
	settings = read_settings_fields(SHIPPING_FIELDS)

	# ponytail: return reasons are read-only here, edit them in Desk until the dashboard
	# grows a child-table editor
	settings["reason_for_return"] = frappe.get_all(
		"Return Reason",
		filters={"parent": SETTINGS_DOCTYPE, "parenttype": SETTINGS_DOCTYPE},
		fields=["name", "display_name", "description"],
		order_by="idx asc",
	)
	return settings


@frappe.whitelist(methods=["POST"])
def save_shipping_settings(**kwargs):
	return write_settings_fields(SHIPPING_FIELDS, kwargs)


@frappe.whitelist()
def get_payment_settings():
	"""Cash on delivery switches and the account the COD charge posts to."""
	return read_settings_fields(PAYMENT_FIELDS)


@frappe.whitelist(methods=["POST"])
def save_payment_settings(**kwargs):
	return write_settings_fields(PAYMENT_FIELDS, kwargs)


@frappe.whitelist()
def get_footer_settings():
	"""Social links, newsletter copy, and the footer trust badges."""
	return read_settings_fields(FOOTER_FIELDS)


@frappe.whitelist(methods=["POST"])
def save_footer_settings(**kwargs):
	return write_settings_fields(FOOTER_FIELDS, kwargs)


def get_advanced_docfields():
	"""Every editable docfield the four curated tabs do not already cover, in layout order.

	Derived from the meta so a newly added field shows up in the dashboard without a code
	change here.
	"""
	docfields = []
	for docfield in frappe.get_meta(SETTINGS_DOCTYPE).fields:
		if docfield.fieldtype in ADVANCED_SKIPPED_FIELDTYPES:
			continue
		if docfield.fieldname in CURATED_FIELDS:
			continue
		if docfield.hidden or docfield.read_only:
			continue
		docfields.append(docfield)

	return docfields


@frappe.whitelist()
def get_advanced_settings():
	"""The long tail of setup fields, grouped by the section they sit under in Desk."""
	frappe.has_permission(SETTINGS_DOCTYPE, ptype="read", throw=True)

	settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
	advanced_fieldnames = {docfield.fieldname for docfield in get_advanced_docfields()}

	groups = []
	group_by_label = {}
	child_tables = []
	current_group_label = "General"

	for docfield in frappe.get_meta(SETTINGS_DOCTYPE).fields:
		if docfield.fieldtype in ("Tab Break", "Section Break"):
			if docfield.label:
				current_group_label = docfield.label
			continue

		if docfield.fieldtype == "Table":
			if docfield.fieldname not in CURATED_FIELDS:
				child_tables.append({"label": docfield.label, "options": docfield.options})
			continue

		if docfield.fieldname not in advanced_fieldnames:
			continue

		group = group_by_label.get(current_group_label)
		if group is None:
			group = {"label": current_group_label, "fields": []}
			group_by_label[current_group_label] = group
			groups.append(group)

		group["fields"].append(
			{
				"fieldname": docfield.fieldname,
				"label": docfield.label,
				"fieldtype": docfield.fieldtype,
				"options": docfield.options,
				"description": docfield.description,
				"value": settings.get(docfield.fieldname),
			}
		)

	return {"groups": groups, "child_tables": child_tables}


@frappe.whitelist(methods=["POST"])
def save_advanced_settings(**kwargs):
	advanced_fieldnames = [docfield.fieldname for docfield in get_advanced_docfields()]
	unknown = set(kwargs) - set(advanced_fieldnames)
	if unknown:
		frappe.throw(frappe._("Not an advanced setting: {0}").format(", ".join(sorted(unknown))))

	return write_settings_fields(advanced_fieldnames, kwargs)


def get_linked_doctypes():
	"""Doctypes reachable through a Lifestyle Settings Link field.

	Bounds get_link_options to the settings form instead of letting it list any doctype.
	"""
	return {
		docfield.options
		for docfield in frappe.get_meta(SETTINGS_DOCTYPE).fields
		if docfield.fieldtype == "Link" and docfield.options
	}


@frappe.whitelist()
def get_link_options(doctype: str, search_text: str | None = None):
	"""Options for a Link control on the settings screen."""
	frappe.has_permission(SETTINGS_DOCTYPE, ptype="read", throw=True)

	if doctype not in get_linked_doctypes():
		frappe.throw(frappe._("{0} is not linked from {1}").format(doctype, SETTINGS_DOCTYPE))

	filters = {}
	if search_text:
		filters["name"] = ("like", f"%{cstr(search_text)}%")

	# ponytail: first 100 matches only - the picker searches server-side, so anything further
	# down is reachable by typing; paginate if a doctype outgrows even a searched list
	records = frappe.get_all(doctype, filters=filters, pluck="name", order_by="name asc", limit=100)
	return [{"label": name, "value": name} for name in records]


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
