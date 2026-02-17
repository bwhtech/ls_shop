# Copyright (c) 2026, and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document

STRIPE_API_BASE = "https://api.stripe.com/v1"


class StripeSettings(Document):
	def create_checkout_session(self, amount, reference_id, currency_code, customer_email, line_item_name="Order Payment"):
		"""Create a Stripe Checkout Session and return session data."""
		secret_key = self.get_password("secret_key").strip()

		# Stripe expects amount in smallest currency unit (e.g., cents/halalas)
		amount_in_subunit = int(round(amount * 100))

		success_url = self.success_url or frappe.utils.get_url(
			f"/en/account/orders/confirmation?payment_mode=stripe&reference_id={reference_id}"
		)
		# Append session_id to success URL
		if "?" in success_url:
			success_url += "&session_id={CHECKOUT_SESSION_ID}"
		else:
			success_url += "?session_id={CHECKOUT_SESSION_ID}"

		cancel_url = self.cancel_url or frappe.utils.get_url(f"/en/cart/checkout")

		payload = {
			"payment_method_types[]": "card",
			"mode": "payment",
			"success_url": success_url,
			"cancel_url": cancel_url,
			"client_reference_id": str(reference_id),
			"customer_email": customer_email,
			"line_items[0][price_data][currency]": currency_code.lower(),
			"line_items[0][price_data][unit_amount]": str(amount_in_subunit),
			"line_items[0][price_data][product_data][name]": line_item_name,
			"line_items[0][quantity]": "1",
		}

		response = requests.post(
			f"{STRIPE_API_BASE}/checkout/sessions",
			data=payload,
			auth=(secret_key, ""),
		)

		if response.status_code != 200:
			frappe.log_error(
				title="Stripe Checkout Session Error",
				message=response.text,
			)
			frappe.throw(_("Failed to create Stripe checkout session. Please try again."))

		return response.json()

	def get_session_status(self, session_id):
		"""Retrieve Stripe Checkout Session status."""
		secret_key = self.get_password("secret_key").strip()

		response = requests.get(
			f"{STRIPE_API_BASE}/checkout/sessions/{session_id}",
			auth=(secret_key, ""),
		)

		if response.status_code != 200:
			frappe.log_error(
				title="Stripe Session Status Error",
				message=response.text,
			)
			frappe.throw(_("Failed to retrieve Stripe session status."))

		return response.json()

	def refund_payment(self, payment_intent_id, amount=None):
		"""Create a refund for a Stripe payment."""
		secret_key = self.get_password("secret_key").strip()

		payload = {
			"payment_intent": payment_intent_id,
		}

		if amount:
			payload["amount"] = int(round(amount * 100))

		response = requests.post(
			f"{STRIPE_API_BASE}/refunds",
			data=payload,
			auth=(secret_key, ""),
		)

		if response.status_code != 200:
			frappe.log_error(
				title="Stripe Refund Error",
				message=response.text,
			)
			frappe.throw(_("Failed to process Stripe refund."))

		return response.json()
