# Copyright (c) 2026, and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StripePaymentRequest(Document):
	def before_save(self):
		if not self.stripe_session_id:
			self.create_session_on_stripe()

	def create_session_on_stripe(self):
		"""Create a Stripe Checkout Session."""
		stripe_settings = frappe.get_cached_doc("Stripe Settings")
		currency_code = self.currency_code or stripe_settings.currency or "SAR"

		session_data = stripe_settings.create_checkout_session(
			amount=self.amount,
			reference_id=self.name or frappe.generate_hash(length=10),
			currency_code=currency_code,
			customer_email=self.customer_email,
			line_item_name=f"Order - {self.ref_docname}",
		)

		self.stripe_session_id = session_data.get("id")
		self.stripe_session_url = session_data.get("url")
		self.stripe_payment_intent = session_data.get("payment_intent")

	def sync_status(self):
		"""Sync payment status from Stripe."""
		stripe_settings = frappe.get_cached_doc("Stripe Settings")
		session_data = stripe_settings.get_session_status(self.stripe_session_id)

		payment_status = session_data.get("payment_status")
		stripe_status = session_data.get("status")

		# Map Stripe status to our status
		if payment_status == "paid":
			self.status = "Paid"
		elif stripe_status == "expired":
			self.status = "Expired"
		elif stripe_status == "complete" and payment_status == "unpaid":
			self.status = "Not Paid"
		elif stripe_status == "open":
			self.status = "Pending"
		else:
			self.status = "Not Paid"

		# Update payment intent
		self.stripe_payment_intent = session_data.get("payment_intent")

		# Get payment method details if available
		if self.stripe_payment_intent and payment_status == "paid":
			self.transaction_reference = self.stripe_payment_intent

		# Check refund status
		if self.refund_amount and self.refund_amount > 0:
			if self.refund_amount >= self.amount:
				self.status = "Refunded"
			else:
				self.status = "Partially Refunded"

		self.flags.ignore_permissions = True
		self.save()

	def refund(self, amount=None):
		"""Process a refund via Stripe."""
		if not self.stripe_payment_intent:
			frappe.throw(_("No payment intent found. Cannot process refund."))

		stripe_settings = frappe.get_cached_doc("Stripe Settings")
		refund_data = stripe_settings.refund_payment(
			payment_intent_id=self.stripe_payment_intent,
			amount=amount,
		)

		refund_amount = refund_data.get("amount", 0) / 100  # Convert from subunit
		self.refund_amount = (self.refund_amount or 0) + refund_amount
		self.sync_status()


def refund_payment_for_payment_entry(doc, event=None):
	"""Hook: Auto-refund Stripe payment when a return Payment Entry is submitted."""
	if doc.mode_of_payment != "Stripe" or doc.payment_type != "Pay":
		return

	payment_request = frappe.get_doc(
		"Stripe Payment Request", {"stripe_session_id": doc.reference_no}
	)
	payment_request.refund(doc.paid_amount)
