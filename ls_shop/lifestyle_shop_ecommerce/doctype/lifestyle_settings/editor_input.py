# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""Trust-boundary helpers shared by the navbar and footer editors.

Both editors take labels and links typed by a shop owner in a Desk dialog and render them into
public storefront pages, so both need the same three checks in the same place.
"""

import frappe
from frappe.utils import validate_url

# A link may point at another page on this store (no scheme) or off-site over http(s). Anything
# else — javascript:, data:, vbscript: — is a script-injection vector once the footer renders it.
SAFE_URL_SCHEMES = ("", "http", "https")


def parse_list(value):
	if isinstance(value, str):
		# Every caller is a Desk dialog posting a JSON array, and orjson raises straight through
		# frappe.parse_json, so malformed input has to become a user-facing error not a 500.
		try:
			value = frappe.parse_json(value)
		except Exception:
			frappe.throw(frappe._("Expected a list, got: {0}").format(value))
	if value is None:
		return []
	return value if isinstance(value, list) else [value]


def require_value(value, message):
	value = (value or "").strip()
	if not value:
		frappe.throw(message)
	return value


def require_safe_url(value, message):
	value = require_value(value, message)
	if not validate_url(value, valid_schemes=SAFE_URL_SCHEMES):
		frappe.throw(frappe._("Link URL {0} uses a scheme that is not allowed.").format(value))
	return value
