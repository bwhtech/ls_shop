# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Sum
from frappe.utils.data import add_days, cint, cstr, flt, formatdate, getdate, strip_html

from ls_shop.api.admin.catalog import get_unpublishable_options
from ls_shop.api.admin.inventory import get_inventory

PAGE_LENGTH = 20

# A page of orders drives four batched lifecycle reads, each with an IN list built from the page.
# Capped so a caller asking for "everything" cannot turn those into IN lists the database chokes on.
MAX_PAGE_LENGTH = 100

# A store owner thinks in "what do I have to do with this order", not in docstatus and
# per_delivered. One map turns ERPNext's state into that question.
OPEN_STATUSES = ("To Deliver and Bill", "To Deliver", "To Bill")

# The fulfilment ladder, read from the top down: an order is described by the furthest rung it has
# reached, so a delivered order never reads back as merely "Packed". Keys are the contract the
# dashboard maps to an icon and a colour; the labels are only ever shown to a person.
STAGE_LABELS = {
	"cancelled": "Cancelled",
	"returned": "Returned",
	"delivered": "Delivered",
	"shipped": "Shipped",
	"fulfilled": "Fulfilled",
	"partly_fulfilled": "Partly fulfilled",
	"packed": "Packed",
	"delivery_note_drafted": "Delivery note drafted",
	"to_fulfil": "To fulfil",
}

# bwh_shipping tracks a parcel in the carrier's vocabulary; the dashboard only cares which rung of
# the ladder that vocabulary lands on. Anything unlisted (Draft, Ready To Ship, Cancelled) is a
# shipment that has not physically moved, so it leaves the stage to the documents underneath it.
SHIPMENT_STAGES = {
	"Delivered": "delivered",
	"RTO": "returned",
	"Pickup Scheduled": "shipped",
	"In Transit": "shipped",
	"Out For Delivery": "shipped",
	"Undelivered": "shipped",
	"Lost": "shipped",
}

# How many rows each Home panel shows before it sends the owner to the full screen.
OVERVIEW_PANEL_LENGTH = 5
OVERVIEW_WINDOW_DAYS = 30


@frappe.whitelist()
def get_orders(
	status: str | None = None, search: str | None = None, start: int = 0, page_length: int = PAGE_LENGTH
):
	"""The whole Orders screen in one call.

	Item counts, payment mode and fulfilment stage are all batched across the page, so the list
	costs the same handful of queries whether it shows one order or a hundred.
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
		page_length=min(cint(page_length) or PAGE_LENGTH, MAX_PAGE_LENGTH),
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

	lifecycles = read_order_lifecycles(order_names)

	return {
		"orders": [
			{
				"name": row.name,
				"customer": row.customer,
				"placed_on": row.transaction_date,
				"status": row.status,
				"state": describe_state(row, lifecycles.get(cstr(row.name))),
				"total": flt(row.grand_total),
				"currency": row.currency,
				"item_count": item_counts.get(row.name, 0),
				"payment_mode": row.custom_ecommerce_payment_mode,
			}
			for row in orders
		],
		"total": total,
	}


def get_address_lines(address_display):
	"""ERPNext builds address_display as HTML, but the dashboard renders it as plain text, so its
	<br> tags used to show up literally on the order screen. Newlines survive the trip because the
	element they land in is whitespace-pre-line."""
	if not address_display:
		return None

	lines = [
		strip_html(part).strip()
		for part in re.split(r"<br\s*/?>", cstr(address_display), flags=re.IGNORECASE)
	]
	return "\n".join(line for line in lines if line) or None


def describe_state(order, lifecycle=None):
	"""Where this order sits on the fulfilment ladder: a stable key plus the owner-facing label.

	The single source of truth behind every order badge in the dashboard. `lifecycle` carries the
	paperwork found for this order by `read_order_lifecycles`; without it the stage is derived from
	the Sales Order alone, which is all the coarse pre-fulfilment rungs need.
	"""
	lifecycle = lifecycle or frappe._dict()
	key = pick_stage(order, lifecycle)
	label = STAGE_LABELS.get(key)
	return {"key": key, "label": _(label) if label else cstr(order.status)}


def pick_stage(order, lifecycle) -> str:
	"""The furthest rung this order has reached, tried from the top of the ladder down."""
	if cint(order.docstatus) == 2:
		return "cancelled"
	if lifecycle.get("stage_from_shipment"):
		return lifecycle.stage_from_shipment
	if lifecycle.get("has_return"):
		return "returned"
	if order.status == "Completed" or flt(order.per_delivered) >= 100:
		return "fulfilled"
	if flt(order.per_delivered) > 0:
		return "partly_fulfilled"
	# Below fulfilment, not above it: ERPNext refuses a Packing Slip against anything but a draft
	# Delivery Note, so packing is what happens on the way to shipping, never after it.
	if lifecycle.get("has_packing_slip"):
		return "packed"
	if lifecycle.get("has_draft_delivery_note"):
		return "delivery_note_drafted"
	if order.status in OPEN_STATUSES:
		return "to_fulfil"
	# An order in a status the ladder has no rung for (On Hold, Closed) keeps ERPNext's own word
	# for it rather than being flattened into a rung it never reached.
	return cstr(order.status)


def read_order_lifecycles(order_names: list) -> dict:
	"""The fulfilment paperwork behind a page of orders, in a fixed number of queries.

	Four reads for the whole page - delivery notes, their headers, packing slips, shipments - rather
	than four per order. Keyed by `cstr(name)` throughout, because an autoincrement-named Sales
	Order comes back as an int here and as a string from the request.
	"""
	if not order_names:
		return {}

	lifecycles = {cstr(name): frappe._dict(delivery_notes=[]) for name in order_names}

	delivery_note_links = frappe.get_all(
		"Delivery Note Item",
		filters={"against_sales_order": ["in", order_names], "docstatus": ["<", 2]},
		fields=["parent", "against_sales_order"],
	)
	orders_by_delivery_note = {}
	for row in delivery_note_links:
		orders_by_delivery_note.setdefault(cstr(row.parent), set()).add(cstr(row.against_sales_order))

	delivery_note_names = list(orders_by_delivery_note)
	if delivery_note_names:
		for note in frappe.get_all(
			"Delivery Note",
			filters={"name": ["in", delivery_note_names]},
			fields=["name", "docstatus", "is_return"],
		):
			for order_name in orders_by_delivery_note.get(cstr(note.name), ()):
				lifecycle = lifecycles.setdefault(order_name, frappe._dict(delivery_notes=[]))
				if cint(note.docstatus) == 1:
					lifecycle.delivery_notes.append(cstr(note.name))
					if cint(note.is_return):
						lifecycle.has_return = True
				else:
					lifecycle.has_draft_delivery_note = True

		for slip in frappe.get_all(
			"Packing Slip",
			filters={"delivery_note": ["in", delivery_note_names], "docstatus": ["<", 2]},
			fields=["delivery_note"],
		):
			for order_name in orders_by_delivery_note.get(cstr(slip.delivery_note), ()):
				lifecycles[order_name].has_packing_slip = True

	read_shipment_stages(order_names, lifecycles)

	for lifecycle in lifecycles.values():
		lifecycle.delivery_notes = sorted(set(lifecycle.delivery_notes))
	return lifecycles


def read_shipment_stages(order_names: list, lifecycles: dict) -> None:
	"""Fold each order's latest carrier status into its lifecycle, in one read.

	Same query shape as `ls_shop.api.shipping.get_order_tracking`, which is what the customer's own
	tracking page reads, so the two screens can never disagree about where a parcel is.
	"""
	from ls_shop.api.shipping import is_connector_installed

	if not is_connector_installed():
		return

	# Newest first, and only the first shipment seen per order counts: an order rebooked after a
	# failed pickup carries a stale older request that would otherwise outrank the live one.
	for request in frappe.get_all(
		"Shipping Request",
		filters={"ref_doctype": "Sales Order", "ref_docname": ["in", order_names], "docstatus": ["<", 2]},
		fields=["ref_docname", "status", "awb"],
		order_by="creation desc",
	):
		lifecycle = lifecycles.get(cstr(request.ref_docname))
		if lifecycle is None or "stage_from_shipment" in lifecycle:
			continue
		lifecycle.stage_from_shipment = SHIPMENT_STAGES.get(cstr(request.status))


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

	lifecycle = read_order_lifecycles([order.name]).get(cstr(order.name), frappe._dict())

	return {
		"name": order.name,
		"customer": order.customer,
		"email": order.contact_email,
		"phone": order.contact_phone,
		"placed_on": order.transaction_date,
		"status": order.status,
		"state": describe_state(order, lifecycle),
		"currency": order.currency,
		"total": flt(order.total),
		"grand_total": flt(order.grand_total),
		"payment_mode": order.custom_ecommerce_payment_mode,
		"shipping_address": get_address_lines(order.address_display),
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
		"deliveries": lifecycle.get("delivery_notes") or [],
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
