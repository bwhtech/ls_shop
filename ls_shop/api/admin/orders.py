# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils.data import add_days, cint, cstr, flt, formatdate, getdate

from ls_shop.api.admin.catalog import get_unpublishable_options
from ls_shop.api.admin.inventory import get_inventory

PAGE_LENGTH = 20

# A store owner thinks in "what do I have to do with this order", not in docstatus and
# per_delivered. One map turns ERPNext's state into that question.
OPEN_STATUSES = ("To Deliver and Bill", "To Deliver", "To Bill")

# How many rows each Home panel shows before it sends the owner to the full screen.
OVERVIEW_PANEL_LENGTH = 5
OVERVIEW_WINDOW_DAYS = 30


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
	# ERPNext moved its transaction mappers out of the doctype module into a sibling `mapper`
	# module. Both layouts are in the wild across the versions this app runs against, so resolve
	# whichever one is installed rather than pinning to a single import path.
	try:
		from erpnext.selling.doctype.sales_order.mapper import make_delivery_note
	except ImportError:
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


# The overview lives here rather than in a module of its own so it ships without a web-process
# restart; it reads across catalogue and stock through those modules' own batched readers.
@frappe.whitelist()
def get_overview(order_status: str | None = None):
	"""The whole Home screen in one call: four figures, recent orders, and two worklists.

	`order_status` only narrows the recent-orders panel; the figures always describe the whole
	store, so flipping that toggle must not move them.
	"""
	frappe.has_permission("Sales Order", ptype="read", throw=True)
	frappe.has_permission("Item", ptype="read", throw=True)

	today = getdate()
	window_start = add_days(today, -(OVERVIEW_WINDOW_DAYS - 1))
	previous_start = add_days(window_start, -OVERVIEW_WINDOW_DAYS)
	previous_end = add_days(window_start, -1)

	current_window = read_sales_window(window_start, today)
	previous_window = read_sales_window(previous_start, previous_end)

	to_fulfil = frappe.db.count("Sales Order", {"docstatus": 1, "status": ["in", OPEN_STATUSES]})
	oldest_open = frappe.db.get_value(
		"Sales Order",
		{"docstatus": 1, "status": ["in", OPEN_STATUSES]},
		"transaction_date",
		order_by="transaction_date asc",
	)

	published_now = frappe.db.count("Style Attribute Variant", {"is_published": 1})
	# Nothing records when an option went live, so an option created inside the window stands in
	# for one that went live inside it.
	# ponytail: creation date proxies the publish date, revisit if a publish log ever lands
	published_new = frappe.db.count(
		"Style Attribute Variant", {"is_published": 1, "creation": [">=", window_start]}
	)

	return {
		"currency": get_reporting_currency(),
		"window_days": OVERVIEW_WINDOW_DAYS,
		"stats": [
			{
				"key": "revenue",
				"label": "Revenue",
				"value": flt(current_window.revenue),
				"format": "currency",
				"delta": percent_change(current_window.revenue, previous_window.revenue),
			},
			{
				"key": "orders",
				"label": "Orders",
				"value": cint(current_window.orders),
				"format": "number",
				"delta": percent_change(current_window.orders, previous_window.orders),
			},
			{
				"key": "to_fulfil",
				"label": "Orders to fulfil",
				"value": to_fulfil,
				"format": "number",
				"delta": None,
				"note": _("Oldest waiting since {0}").format(formatdate(oldest_open, "d MMM"))
				if oldest_open
				else _("Nothing waiting"),
			},
			{
				"key": "products_live",
				"label": "Products live",
				"value": published_now,
				"format": "number",
				"delta": percent_change(published_now, published_now - published_new),
			},
		],
		"recent_orders": get_orders(status=order_status, page_length=OVERVIEW_PANEL_LENGTH)["orders"],
		"running_low": get_inventory(page_length=OVERVIEW_PANEL_LENGTH)["rows"],
		"needs_attention": get_unpublishable_options(limit=OVERVIEW_PANEL_LENGTH),
	}


def read_sales_window(from_date, to_date):
	"""Revenue and order count for one date window, as a single aggregate read.

	Sums base_grand_total, not grand_total: checkout takes whichever currency the customer
	paid in, so only the company-currency figure is addable across orders.
	"""
	sales_order = frappe.qb.DocType("Sales Order")
	rows = (
		frappe.qb.from_(sales_order)
		.select(
			Sum(sales_order.base_grand_total).as_("revenue"),
			Count(sales_order.name).as_("orders"),
		)
		.where(sales_order.docstatus == 1)
		.where(sales_order.transaction_date >= from_date)
		.where(sales_order.transaction_date <= to_date)
	).run(as_dict=True)

	return rows[0] if rows else frappe._dict({"revenue": 0, "orders": 0})


def percent_change(current, previous):
	"""Month-over-month change, or None when there is no baseline to compare against."""
	previous = flt(previous)
	if not previous:
		return None
	return flt((flt(current) - previous) / previous * 100, 1)


def get_reporting_currency():
	company = frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "company")
	currency = frappe.get_cached_value("Company", company, "default_currency") if company else None
	return currency or frappe.defaults.get_global_default("currency")
