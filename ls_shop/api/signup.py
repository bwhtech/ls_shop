import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint

from ls_shop.core import send_otp


def verify_otp(email: str, otp: str):
	"""Check the OTP and burn it.

	Replay is the whole risk here: the key used to survive the full cache TTL, so one intercepted code
	stayed valid for every later attempt. cint keeps a non-numeric code a clean "Invalid OTP" rather
	than an uncaught ValueError.
	"""
	cache_key = f"otp:{email}"
	stored_otp = frappe.cache.get_value(cache_key)
	if not stored_otp or cint(otp) != cint(stored_otp):
		frappe.throw(_("Invalid OTP"))

	frappe.cache.delete_value(cache_key)


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=60 * 60)
def send_signup_otp(email: str):
	user_exist = frappe.db.exists("User", {"email": email})
	if user_exist:
		frappe.throw(_("Email already in use."))
	send_otp(email)


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=60 * 60)
def send_login_otp(email: str):
	user_exists = frappe.db.exists("User", email)
	if not user_exists:
		frappe.throw(_("Invalid login ID"))

	send_otp(email)


@frappe.whitelist(allow_guest=True)
# Keyed on email, not the default caller IP: an IP-bound limit leaves a 6-digit code brute-forceable
# from a pool of addresses inside its own validity window.
@rate_limit(key="email", limit=5, seconds=60 * 5)
def verify_signup_otp(email: str, first_name: str, last_name: str, otp: str):
	verify_otp(email, otp)

	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"enabled": 1,
		}
	)
	user.insert(ignore_permissions=True)

	frappe.local.login_manager.login_as(email)


@frappe.whitelist(allow_guest=True)
@rate_limit(key="email", limit=5, seconds=60 * 5)
def verify_login_otp(email: str, otp: str):
	"""Check OTP from Redis instead of DB"""

	verify_otp(email, otp)
	frappe.local.login_manager.login_as(email)
