import frappe
from bwh_payments.currency import to_minor_units
from frappe import _
from frappe.utils.data import flt, fmt_money

from ls_shop.api.payments import get_charge_amount, place_order


def on_payment_request_update(doc, method=None):
	"""Turn a paid gateway request into a Sales Order, exactly once per payment."""
	if doc.status != "Paid" or doc.ref_doctype != "Quotation":
		return

	# The Quotation docstatus is the durable idempotency token: place_order submits it, so a replayed
	# webhook and a confirm_payment poll racing in separate requests cannot both create an order. The
	# in-memory flag this replaces only guarded re-entry inside one request.
	if frappe.db.get_value("Quotation", doc.ref_docname, "docstatus", for_update=True) != 0:
		return

	quotation = frappe.get_doc("Quotation", doc.ref_docname)
	validate_charged_amount_matches_cart(quotation, doc)
	sales_order = place_order(
		quotation,
		payment_mode=doc.gateway,
		gateway_amount=flt(doc.amount),
		gateway_reference=doc.order_ref,
	)

	# Repointed with db_set rather than save() so this hook does not re-enter on its own write.
	doc.db_set({"ref_doctype": "Sales Order", "ref_docname": sales_order.name}, update_modified=False)


def validate_charged_amount_matches_cart(quotation, payment_request):
	"""Refuse to ship a cart that no longer costs what the gateway charged for it.

	The gateway session freezes an amount, but ref_docname points at the shopper's live draft cart, which
	stays editable while the session is open. Without this a 300 session submits a 3000 order and the
	goods leave the warehouse against 300 of real money. Reconcile or refund — never ship.
	"""
	currency = payment_request.currency_code
	cart_amount = get_charge_amount(quotation)
	charged_amount = flt(payment_request.amount)
	# Minor units, because two float totals that render identically are routinely not `==`.
	if to_minor_units(cart_amount, currency) == to_minor_units(charged_amount, currency):
		return

	frappe.throw(
		_(
			"Order {0} now totals {1} but only {2} was collected. The order has not been placed;"
			" reconcile or refund the payment before releasing any goods."
		).format(
			quotation.name,
			fmt_money(cart_amount, currency=currency),
			fmt_money(charged_amount, currency=currency),
		),
		title=_("Paid Amount Does Not Match The Order"),
	)
