no_cache = True

import frappe

from ls_shop.utils import get_login_url_for_current_page


def get_context(context):
	# The gateway sends the shopper back here with the money already taken, and confirm_payment is
	# whitelisted for signed-in shoppers only - it scopes the lookup to frappe.session.user, so it
	# cannot be opened to Guest. Without a session frappe.is_whitelisted refuses the call with a bare
	# "not whitelisted", which reads as a broken store to somebody who has just been charged.
	if frappe.session.user == "Guest":
		context.login_url = get_login_url_for_current_page()
	return context
