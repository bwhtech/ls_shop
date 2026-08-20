# The data layer is not duplicated: www.account.orders.detail.get_context already resolves the
# order behind get_orders_list's `sales_order.owner == frappe.session.user` filter, the return
# period and the return reasons, so the themed page only re-skins what it hands back.
no_cache = True

import frappe

from ls_shop.www.account.orders import detail


def get_context(context):
	detail.get_context(context)
	# The line items arrive as a JSON_ARRAYAGG string from the SQL layer; parsing them here
	# keeps the template free of a json global the theme jinja environment does not expose.
	context.order_items = frappe.parse_json(context.order.get("items")) or []
	context.invoice_name = get_invoice_name(context.order.name)
	context.print_format = (
		frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "print_format") or "Standard"
	)
	return context


def get_invoice_name(order_id):
	invoices = frappe.get_all("Sales Invoice", filters={"sales_order": order_id}, pluck="name", limit=1)
	return invoices[0] if invoices else None
