# The data layer is not duplicated: www.account.orders.index.get_orders_list already scopes every
# row to `sales_order.owner == frappe.session.user`, so an order_id belonging to somebody else -
# or a stale one that no longer resolves - simply comes back empty instead of leaking an order.
no_cache = True

import frappe

from ls_shop.www.account.orders.index import get_orders_list


def get_context(context):
	if frappe.session.user == "Guest":
		raise frappe.PermissionError
	context.order = get_owned_order(frappe.form_dict.get("order_id"))
	return context


def get_owned_order(order_id):
	if not order_id:
		return None
	_, orders = get_orders_list([order_id])
	return orders[0] if orders else None
