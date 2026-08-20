# The data layer is not duplicated: www.account.orders.index.get_orders_list already scopes every
# row to `sales_order.owner == frappe.session.user`, so an order_id belonging to somebody else -
# or a stale one that no longer resolves - simply comes back empty instead of leaking an order.
no_cache = True

import frappe

from ls_shop.utils import get_login_url_for_current_page
from ls_shop.www.account.orders.index import get_orders_list


def get_context(context):
	context.no_cache = 1
	# Unlike every other account page this one is the gateway return URL, so a shopper whose session
	# expired during checkout lands here having already been charged. confirm_payment cannot be opened
	# to Guest - it scopes the lookup to frappe.session.user - so the page asks for the login instead
	# of letting the API refuse with a bare "not whitelisted".
	if frappe.session.user == "Guest":
		context.login_url = get_login_url_for_current_page()
		return context

	context.order = get_owned_order(frappe.form_dict.get("order_id"))
	return context


def get_owned_order(order_id):
	if not order_id:
		return None
	_, orders = get_orders_list([order_id])
	return orders[0] if orders else None
