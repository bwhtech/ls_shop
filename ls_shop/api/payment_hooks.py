import frappe
from frappe.utils.data import flt

from ls_shop.api.payments import place_order


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
	sales_order = place_order(
		quotation,
		payment_mode=doc.gateway,
		gateway_amount=flt(doc.amount),
		gateway_reference=doc.order_ref,
	)

	# Repointed with db_set rather than save() so this hook does not re-enter on its own write.
	doc.db_set({"ref_doctype": "Sales Order", "ref_docname": sales_order.name}, update_modified=False)
