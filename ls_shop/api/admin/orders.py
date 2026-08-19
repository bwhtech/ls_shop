# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.data import cint, cstr, flt

PAGE_LENGTH = 20

# A store owner thinks in "what do I have to do with this order", not in docstatus and
# per_delivered. One map turns ERPNext's state into that question.
OPEN_STATUSES = ("To Deliver and Bill", "To Deliver", "To Bill")


@frappe.whitelist()
def get_orders(
	status: str | None = None, search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH
):
	"""The whole Orders screen in one call.

	Item counts, payment mode and fulfilment progress are all batched across the page, so the
	list costs the same three queries whether it shows one order or a hundred.
	"""
	frappe.has_permission("Sales Order", ptype="read", throw=True)

	filters = {"docstatus": ["<", 2]}
	if status == "open":
		filters["status"] = ["in", OPEN_STATUSES]
	elif status == "fulfilled":
		filters["status"] = "Completed"
	elif status == "cancelled":
		filters = {"docstatus": 2}
	if search:
		filters["name"] = ["like", f"%{search}%"]

	total = frappe.db.count("Sales Order", filters)
	orders = frappe.get_all(
		"Sales Order",
		filters=filters,
		fields=[
			"name",
			"customer",
			"transaction_date",
			"status",
			"grand_total",
			"currency",
			"per_delivered",
			"docstatus",
			"custom_ecommerce_payment_mode",
		],
		order_by="creation desc",
		start=cint(start),
		page_length=cint(page_length) or PAGE_LENGTH,
	)
	if not orders:
		return {"orders": [], "total": total}

	order_names = [row.name for row in orders]
	item_counts = {}
	for row in frappe.get_all(
		"Sales Order Item",
		filters={"parent": ["in", order_names]},
		fields=["parent", "qty"],
	):
		item_counts[row.parent] = item_counts.get(row.parent, 0) + flt(row.qty)

	return {
		"orders": [
			{
				"name": row.name,
				"customer": row.customer,
				"placed_on": row.transaction_date,
				"status": row.status,
				"state": describe_state(row),
				"total": flt(row.grand_total),
				"currency": row.currency,
				"item_count": item_counts.get(row.name, 0),
				"payment_mode": row.custom_ecommerce_payment_mode,
			}
			for row in orders
		],
		"total": total,
	}


def describe_state(order):
	"""What the owner has to do next, in their words."""
	if cint(order.docstatus) == 2:
		return "Cancelled"
	if order.status == "Completed":
		return "Fulfilled"
	if flt(order.per_delivered) > 0:
		return "Partly fulfilled"
	if order.status in OPEN_STATUSES:
		return "To fulfil"
	return order.status


@frappe.whitelist()
def get_order(sales_order: str):
	"""Everything one order's screen needs, in one call."""
	frappe.has_permission("Sales Order", doc=sales_order, ptype="read", throw=True)

	order = frappe.db.get_value(
		"Sales Order",
		sales_order,
		[
			"name",
			"customer",
			"contact_email",
			"contact_phone",
			"transaction_date",
			"status",
			"docstatus",
			"currency",
			"total",
			"grand_total",
			"per_delivered",
			"custom_ecommerce_payment_mode",
			"shipping_address",
			"address_display",
		],
		as_dict=True,
	)
	if not order:
		frappe.throw(_("Order {0} not found").format(sales_order))

	items = frappe.get_all(
		"Sales Order Item",
		filters={"parent": sales_order},
		fields=["item_code", "item_name", "qty", "delivered_qty", "rate", "amount", "image"],
		order_by="idx asc",
	)

	# The size lives on the variant's child row, not on the order line, so one batched lookup
	# turns item codes into something a person can read off a picking list.
	sizes_by_item_code = {}
	item_codes = [row.item_code for row in items if row.item_code]
	if item_codes:
		for row in frappe.get_all(
			"Color Size Item",
			filters={"item_code": ["in", item_codes], "parenttype": "Style Attribute Variant"},
			fields=["item_code", "size", "parent"],
		):
			sizes_by_item_code.setdefault(cstr(row.item_code), row.size)

	deliveries = frappe.get_all(
		"Delivery Note Item",
		filters={"against_sales_order": sales_order, "docstatus": 1},
		fields=["parent", "item_code", "qty"],
	)

	return {
		"name": order.name,
		"customer": order.customer,
		"email": order.contact_email,
		"phone": order.contact_phone,
		"placed_on": order.transaction_date,
		"status": order.status,
		"state": describe_state(order),
		"currency": order.currency,
		"total": flt(order.total),
		"grand_total": flt(order.grand_total),
		"payment_mode": order.custom_ecommerce_payment_mode,
		"shipping_address": order.address_display,
		"can_fulfil": cint(order.docstatus) == 1 and flt(order.per_delivered) < 100,
		"items": [
			{
				"item_code": row.item_code,
				"title": row.item_name,
				"size": sizes_by_item_code.get(cstr(row.item_code)),
				"qty": flt(row.qty),
				"delivered_qty": flt(row.delivered_qty),
				"rate": flt(row.rate),
				"amount": flt(row.amount),
				"image": row.image,
			}
			for row in items
		],
		"deliveries": sorted({row.parent for row in deliveries}),
	}


@frappe.whitelist(methods=["POST"])
def fulfil_order(sales_order: str):
	"""Ship what is still outstanding on an order.

	Delegates to ERPNext's own Sales Order -> Delivery Note mapper rather than hand-building the
	document, so pricing, taxes and the delivered-quantity bookkeeping stay ERPNext's problem.
	"""
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

	frappe.has_permission("Sales Order", doc=sales_order, ptype="submit", throw=True)
	frappe.has_permission("Delivery Note", ptype="create", throw=True)

	order = frappe.get_doc("Sales Order", sales_order)
	if order.docstatus != 1:
		frappe.throw(_("Only a confirmed order can be fulfilled."))
	if flt(order.per_delivered) >= 100:
		frappe.throw(_("This order has already been fulfilled."))

	delivery_note = make_delivery_note(sales_order)
	delivery_note.insert()
	delivery_note.submit()

	return {"delivery_note": delivery_note.name}
