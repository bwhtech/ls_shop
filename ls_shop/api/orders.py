import frappe
from frappe import _
from frappe.utils import flt

from ls_shop.api.payments import system_user_session
from ls_shop.utils import validate_document_access


@frappe.whitelist()
def cancel_order(order_id: str):
	order_doc = frappe.get_doc("Sales Order", order_id)
	validate_can_cancel(order_doc)
	if order_doc.custom_ecommerce_payment_mode != "COD":
		# The helper still clamps: a staff partial refund then this cancellation would pay out twice.
		make_refund_payment_entry(order_id)

	order_doc.flags.ignore_permissions = True
	if order_doc.docstatus == 1:
		order_doc.cancel()
	elif order_doc.docstatus == 0:
		order_doc.submit()
		order_doc.reload()
		order_doc.cancel()


def resolve_refund_amount(refundable_amount: float, amount: float | None) -> float:
	"""Clamp a requested refund to what the order still owes back. Only `None` means "the balance":
	a non-numeric post coerces to 0, and `or` would read that as unspecified and pay out the max."""
	precision = frappe.get_precision("Payment Entry", "paid_amount")
	refundable_amount = flt(refundable_amount, precision)
	refund_amount = refundable_amount if amount is None else flt(amount, precision)

	if refund_amount <= 0 or refund_amount > refundable_amount:
		frappe.throw(_("Refund amount must be between 0 and {0}.").format(refundable_amount))

	return refund_amount


def make_refund_payment_entry(order_id: str, amount: float | None = None) -> str:
	"""Submit the Payment Entry that reverses a paid order. Callers must authorize access first."""
	# Without this lock two concurrent refunds both see the pre-refund balance and both pay out.
	frappe.get_doc("Sales Order", order_id).lock()

	refund_status = get_refund_status(order_id)
	if not refund_status.get("can_refund"):
		frappe.throw(_("This order cannot be refunded."))

	refund_amount = resolve_refund_amount(refund_status["refundable_amount"], amount)

	payment_entry = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": "Sales Order", "reference_name": order_id},
		fields=["parent"],
		# Ordered so a second gateway attempt cannot change which entry the refund is modelled on.
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
				"paid_to": payment_entry_doc.paid_from,
				"paid_amount": refund_amount,
				# received_amount unset: set_received_amount derives it; hardcoding asserts a wrong 1:1 rate.
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
	# The Desk dialog's bound is browser-side only; make_refund_payment_entry clamps for real.
	frappe.has_permission("Sales Order", ptype="write", doc=order_id, throw=True)

	return make_refund_payment_entry(order_id, amount)


def validate_can_cancel(order_doc):
	if order_doc.docstatus > 1:
		frappe.throw(_("Order already cancelled!"))

	if order_doc.status == "To Bill":
		frappe.throw(_("Order already shipped!"))

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
			# Gateways reuse reference numbers across parties; an unscoped match pulls in another's refund.
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
