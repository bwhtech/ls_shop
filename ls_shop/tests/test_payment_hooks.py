# Copyright (c) 2026, company@bwhstudios.com and Contributors
# Real-DB tests for the paid-gateway-callback hook (api/payment_hooks.py). The Quotation docstatus is
# the idempotency token, so these drive the hook twice against persisted state and count rows.

from unittest.mock import patch

import frappe
from bwh_payments.bwh_payments.doctype.gateway_payment_request.test_gateway_payment_request import (
	GATEWAY,
	configure_stripe_gateway,
)
from bwh_payments.bwh_payments.doctype.stripe_gateway_settings import stripe_gateway_settings
from bwh_payments.tests.fake_stripe import FakeStripeClient
from frappe.tests import IntegrationTestCase
from frappe.utils import get_year_ending, get_year_start, getdate

from ls_shop.api.payment_hooks import on_payment_request_update

COMPANY = "Lifestyle Demo"
ITEM_GROUP = "Interior Accessories"
DEFAULT_CASH_ACCOUNT = "Cash - LSD"
CURRENCY = "SAR"
# The site's stock selling list is in INR; a list in the company currency keeps the fixture off the
# Currency Exchange table, which has nothing to do with what these tests prove.
PRICE_LIST = "ZZ Payhook SAR Selling"
ITEM_RATE = 150.0


class TestPaymentHookIdempotency(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# get_single hands back a cached copy whose timestamp is older than the row another test class
		# already wrote in this process, which save() then rejects with a TimestampMismatchError.
		frappe.clear_cache()
		configure_stripe_gateway()
		cls.ensure_mode_of_payment()
		cls.ensure_price_list()
		cls.ensure_fiscal_year()

	def setUp(self):
		FakeStripeClient.reset()
		# The gateway transport is the only true external boundary here; everything else is real.
		stripe_client_patch = patch.object(stripe_gateway_settings.stripe, "StripeClient", FakeStripeClient)
		stripe_client_patch.start()
		self.addCleanup(stripe_client_patch.stop)

		self.item_code = self.create_item()
		self.customer = self.create_customer()
		self.contact_email = self.create_contact(self.customer)
		self.quotation = self.create_cart_quotation()
		self.payment_request = self.create_paid_payment_request(self.quotation)

	# -- fixtures ---------------------------------------------------------------------------------

	@classmethod
	def ensure_mode_of_payment(cls):
		"""place_order throws unless a Mode of Payment shares the gateway's exact name."""
		if not frappe.db.exists("Mode of Payment", GATEWAY):
			frappe.get_doc(
				{"doctype": "Mode of Payment", "mode_of_payment": GATEWAY, "enabled": 1, "type": "Bank"}
			).insert(ignore_permissions=True)

		# get_default_bank_cash_account refuses to post a Payment Entry without this row.
		mode_of_payment = frappe.get_doc("Mode of Payment", GATEWAY)
		if not any(row.company == COMPANY for row in mode_of_payment.accounts):
			mode_of_payment.append("accounts", {"company": COMPANY, "default_account": DEFAULT_CASH_ACCOUNT})
			mode_of_payment.save(ignore_permissions=True)

	@classmethod
	def ensure_fiscal_year(cls):
		"""This site was never given one, and every submitted accounting document needs one."""
		year_start = get_year_start(getdate())
		if frappe.db.exists("Fiscal Year", {"year_start_date": year_start, "disabled": 0}):
			return
		frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": str(year_start.year),
				"year_start_date": year_start,
				"year_end_date": get_year_ending(getdate()),
			}
		).insert(ignore_permissions=True, ignore_if_duplicate=True)

	@classmethod
	def ensure_price_list(cls):
		if frappe.db.exists("Price List", PRICE_LIST):
			return
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": PRICE_LIST,
				"currency": CURRENCY,
				"selling": 1,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	def create_item(self):
		item_code = f"ZZ-PAYHOOK-{frappe.generate_hash(length=8)}"
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "ZZ Payment Hook Item",
				"item_group": ITEM_GROUP,
				"stock_uom": "Nos",
				# Non-stock keeps the Sales Invoice off the stock ledger; the hook is what is under test.
				"is_stock_item": 0,
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": PRICE_LIST,
				"price_list_rate": ITEM_RATE,
			}
		).insert(ignore_permissions=True)
		return item_code

	def create_customer(self):
		return (
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": f"ZZ Payhook Customer {frappe.generate_hash(length=8)}",
					"customer_type": "Individual",
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	def create_contact(self, customer):
		email_id = f"zz_payhook_{frappe.generate_hash(length=8)}@example.com"
		contact = frappe.get_doc(
			{
				"doctype": "Contact",
				"first_name": "ZZ Payhook",
				"email_ids": [{"email_id": email_id, "is_primary": 1}],
				"phone_nos": [{"phone": "+966500000000", "is_primary_phone": 1}],
				"links": [{"link_doctype": "Customer", "link_name": customer}],
			}
		).insert(ignore_permissions=True)
		self.contact_person = contact.name
		return email_id

	def create_cart_quotation(self):
		quotation = frappe.new_doc("Quotation")
		quotation.update(
			{
				"quotation_to": "Customer",
				"party_name": self.customer,
				"company": COMPANY,
				"order_type": "Shopping Cart",
				"contact_person": self.contact_person,
				# The storefront stamps the shopper's login here; ownership checks read it back.
				"contact_email": self.contact_email,
				"currency": CURRENCY,
				"conversion_rate": 1,
				"selling_price_list": PRICE_LIST,
				"price_list_currency": CURRENCY,
				"plc_conversion_rate": 1,
				"items": [{"item_code": self.item_code, "qty": 2}],
			}
		)
		quotation.flags.ignore_permissions = True
		quotation.insert()
		return quotation

	def create_paid_payment_request(self, quotation):
		payment_request = frappe.get_doc(
			{
				"doctype": "Gateway Payment Request",
				"gateway": GATEWAY,
				"amount": quotation.grand_total,
				"currency_code": quotation.currency,
				"company": COMPANY,
				"ref_doctype": "Quotation",
				"ref_docname": quotation.name,
				"customer_ref": quotation.party_name,
				"customer_email": self.contact_email,
			}
		).insert(ignore_permissions=True)

		FakeStripeClient.register_paid_session(
			payment_request.order_ref, payment_request.currency_code.lower()
		)
		# db_set, not save(), so flipping to Paid does not itself fire the hook under test.
		payment_request.db_set("status", "Paid", update_modified=False)
		payment_request.reload()
		return payment_request

	# -- queries ----------------------------------------------------------------------------------

	def submitted_sales_orders(self):
		return frappe.get_all(
			"Sales Order Item",
			filters={"prevdoc_docname": self.quotation.name, "docstatus": 1},
			pluck="parent",
			distinct=True,
		)

	def submitted_sales_invoices(self, sales_order):
		return frappe.get_all(
			"Sales Invoice Item",
			filters={"sales_order": sales_order, "docstatus": 1},
			pluck="parent",
			distinct=True,
		)

	def submitted_payment_entries(self, sales_invoice):
		return frappe.get_all(
			"Payment Entry Reference",
			filters={"reference_doctype": "Sales Invoice", "reference_name": sales_invoice, "docstatus": 1},
			pluck="parent",
			distinct=True,
		)

	# -- tests ------------------------------------------------------------------------------------

	def test_a_paid_payment_creates_one_sales_order_and_one_sales_invoice(self):
		on_payment_request_update(self.payment_request)

		sales_orders = self.submitted_sales_orders()
		self.assertEqual(len(sales_orders), 1)
		self.assertEqual(frappe.db.get_value("Quotation", self.quotation.name, "docstatus"), 1)

		sales_invoices = self.submitted_sales_invoices(sales_orders[0])
		self.assertEqual(len(sales_invoices), 1)

		payment_entries = self.submitted_payment_entries(sales_invoices[0])
		self.assertEqual(len(payment_entries), 1)
		self.assertEqual(
			frappe.db.get_value("Payment Entry", payment_entries[0], "reference_no"),
			self.payment_request.order_ref,
		)
		self.assertEqual(frappe.db.get_value("Payment Entry", payment_entries[0], "mode_of_payment"), GATEWAY)

	def test_a_duplicate_callback_does_not_create_a_second_order(self):
		"""A replayed webhook racing a confirm_payment poll must not bill the shopper twice."""
		on_payment_request_update(self.payment_request)
		first_sales_orders = self.submitted_sales_orders()

		# The second delivery still carries the original Quotation reference, exactly as the gateway
		# would replay it; only the persisted docstatus can stop it.
		replayed = frappe.get_doc("Gateway Payment Request", self.payment_request.name)
		replayed.ref_doctype = "Quotation"
		replayed.ref_docname = self.quotation.name
		on_payment_request_update(replayed)

		# Without the docstatus guard the replay re-enters place_order and dies inside the Sales Order
		# insert, so simply letting this call run unwrapped is part of the assertion.
		self.assertEqual(self.submitted_sales_orders(), first_sales_orders)
		self.assertEqual(len(self.submitted_sales_orders()), 1)

		sales_invoices = self.submitted_sales_invoices(first_sales_orders[0])
		self.assertEqual(len(sales_invoices), 1)
		self.assertEqual(len(self.submitted_payment_entries(sales_invoices[0])), 1)

		# Any docstatus, so a half-finished replay that only got as far as a draft is still caught.
		self.assertEqual(frappe.db.count("Sales Order", {"customer": self.customer}), 1)
		self.assertEqual(frappe.db.count("Sales Invoice", {"customer": self.customer}), 1)

	def test_saving_the_request_as_paid_fires_the_hook_through_doc_events(self):
		"""Everything else calls the hook directly; this proves the hooks.py wiring reaches it."""
		payment_request = frappe.get_doc(
			{
				"doctype": "Gateway Payment Request",
				"gateway": GATEWAY,
				"amount": self.quotation.grand_total,
				"currency_code": self.quotation.currency,
				"company": COMPANY,
				"ref_doctype": "Quotation",
				"ref_docname": self.quotation.name,
				"customer_ref": self.quotation.party_name,
				"customer_email": self.contact_email,
			}
		).insert(ignore_permissions=True)
		FakeStripeClient.register_paid_session(payment_request.order_ref, CURRENCY.lower())

		payment_request.status = "Paid"
		payment_request.save(ignore_permissions=True)

		self.assertEqual(len(self.submitted_sales_orders()), 1)
		self.assertEqual(payment_request.ref_doctype, "Sales Order")

	def test_the_payment_request_is_repointed_at_the_sales_order(self):
		on_payment_request_update(self.payment_request)

		reference = frappe.db.get_value(
			"Gateway Payment Request",
			self.payment_request.name,
			["ref_doctype", "ref_docname"],
			as_dict=True,
		)
		self.assertEqual(reference.ref_doctype, "Sales Order")
		self.assertEqual(reference.ref_docname, self.submitted_sales_orders()[0])
