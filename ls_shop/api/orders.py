import frappe
from frappe import _
from frappe.utils import flt

from ls_shop.api.payments import system_user_session
from ls_shop.utils import validate_document_access


@frappe.whitelist()
def cancel_order(order_id: str):
	# check if can cancel
	order_doc = frappe.get_doc("Sales Order", order_id)
	validate_can_cancel(order_doc)
	if order_doc.custom_ecommerce_payment_mode != "COD":
		# validate_can_cancel has already established the caller owns this order, so the refund goes
		# through the internal helper rather than the staff-facing endpoint. The helper still clamps:
		# a staff partial refund followed by this cancellation would otherwise pay the original amount
		# out a second time.
		make_refund_payment_entry(order_id)

	order_doc.flags.ignore_permissions = True
	if order_doc.docstatus == 1:
		order_doc.cancel()
	elif order_doc.docstatus == 0:
		order_doc.submit()
		order_doc.reload()  # Ensure the document state is updated
		order_doc.cancel()


def resolve_refund_amount(refundable_amount: float, amount: float | None) -> float:
	"""Clamp a requested refund to what the order still owes back.

	`amount` arrives from a form post, so a non-numeric value coerces to 0 rather than raising. `or`
	would read that 0 as "unspecified" and pay out the maximum, which is why None is the only thing
	that means "refund the balance".
	"""
	precision = frappe.get_precision("Payment Entry", "paid_amount")
	refundable_amount = flt(refundable_amount, precision)
	refund_amount = refundable_amount if amount is None else flt(amount, precision)

	if refund_amount <= 0 or refund_amount > refundable_amount:
		frappe.throw(_("Refund amount must be between 0 and {0}.").format(refundable_amount))

	return refund_amount


def make_refund_payment_entry(order_id: str, amount: float | None = None) -> str:
	"""Submit the Payment Entry that reverses a paid order. Callers must authorize access first.

	The clamp lives here, not in the whitelisted wrapper, because cancel_order refunds on the
	customer's behalf — a limit enforced at one of two entry points is not a limit.
	"""
	# get_refund_status reads what has already been paid back, so without the row lock two concurrent
	# refunds both see the pre-refund balance and both pay out in full.
	frappe.get_doc("Sales Order", order_id).lock()

	refund_status = get_refund_status(order_id)
	if not refund_status.get("can_refund"):
		frappe.throw(_("This order cannot be refunded."))

	refund_amount = resolve_refund_amount(refund_status["refundable_amount"], amount)

	payment_entry = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Order", "reference_name": order_id},
		fields=["parent"],
		# Ordered so a second gateway attempt or a partial payment cannot change which entry the
		# refund is modelled on.
		order_by="creation asc",
		limit=1,
	)

	if not payment_entry:
		frappe.throw(_("No Payment Entry found for this Sales Order."))

	payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry[0].parent)

	with system_user_session():
		new_payment_entry = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Pay",
				"mode_of_payment": payment_entry_doc.mode_of_payment,
				"party_type": payment_entry_doc.party_type,
				"party": payment_entry_doc.party,
				"company": payment_entry_doc.company,
				"paid_from": payment_entry_doc.paid_to,
				"paid_to": payment_entry_doc.paid_from,  # Make sure refund flows back
				"paid_amount": refund_amount,
				# received_amount is deliberately not set: PaymentEntry.set_received_amount derives it,
				# and hardcoding it asserts a 1:1 rate that is wrong the moment the party account is in
				# another currency.
				"reference_no": payment_entry_doc.reference_no,
				"reference_date": frappe.utils.nowdate(),
				"remarks": f"Refund for Sales Order {order_id}",
			}
		)
		new_payment_entry.insert(ignore_permissions=True)
		new_payment_entry.submit()

	return new_payment_entry.name


@frappe.whitelist()
def create_refund_payment_entry(order_id: str, amount: float | None = None) -> str:
	"""Refund an order from the Sales Order form. Staff only."""
	# The Desk dialog bounds the amount before it calls, but that check lives in the browser — a direct
	# POST would otherwise name any figure. make_refund_payment_entry clamps it for real.
	frappe.has_permission("Sales Order", ptype="write", doc=order_id, throw=True)

	return make_refund_payment_entry(order_id, amount)


def validate_can_cancel(order_doc):
	if order_doc.docstatus > 1:
		frappe.throw(_("Order already cancelled!"))

	# If already shipped, can't
	if order_doc.status == "To Bill":
		frappe.throw(_("Order already shipped!"))

	# If already completed, can't
	if order_doc.status == "Completed":
		frappe.throw(_("Order already delivered!"))

	if order_doc.owner != frappe.session.user:
		frappe.throw(_("Action not allowed"))


def get_refund_status(order_id: str) -> dict:
	"""Refund math for one order. Callers must authorize access first."""
	order = frappe.get_doc("Sales Order", order_id)
	if order.custom_ecommerce_payment_mode == "COD":
		return {"can_refund": False}

	payment_entry = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Order", "reference_name": order_id},
		fields=["parent"],
		limit=1,
	)
	if not payment_entry:
		return {"can_refund": False}
	payment_entry_doc = frappe.get_doc("Payment Entry", payment_entry[0].parent)

	refund_payment_entries = frappe.get_all(
		"Payment Entry",
		filters={
			"payment_type": "Pay",
			"reference_no": payment_entry_doc.reference_no,
			# Gateways reuse reference numbers across parties, so an unscoped match pulls in someone
			# else's refund and silently blocks a legitimate one.
			"party_type": payment_entry_doc.party_type,
			"party": payment_entry_doc.party,
			"company": payment_entry_doc.company,
			"docstatus": 1,
		},
		fields=["paid_amount"],
	)

	total_refunded = sum(flt(pe.paid_amount) for pe in refund_payment_entries)

	if total_refunded >= order.rounded_total:
		return {
			"can_refund": False,
		}

	# Determine refundable balance
	only_charges = total_refunded >= order.net_total
	refundable_amount = order.rounded_total - total_refunded

	return {
		"can_refund": True,
		"only_charges": only_charges,
		"amount_refunded": total_refunded,
		"refundable_amount": refundable_amount,
	}


@frappe.whitelist()
def get_sales_order_refund_status(order_id: str):
	validate_document_access("Sales Order", order_id)
	return get_refund_status(order_id)
