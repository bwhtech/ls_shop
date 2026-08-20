# Copyright (c) 2026, company@bwhstudios.com and Contributors
# Tests for the fulfilment ladder behind every order badge in the store-admin dashboard
# (api/admin/orders.py). The ladder is pure, so it is exercised without touching the database;
# the batched reader that feeds it is covered against real documents.

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase

from ls_shop.api.admin.orders import (
	STAGE_LABELS,
	describe_state,
	get_address_lines,
	read_order_lifecycles,
)


def make_order(**values):
	order = frappe._dict({"docstatus": 1, "status": "To Deliver", "per_delivered": 0})
	order.update(values)
	return order


class TestFulfilmentLadder(UnitTestCase):
	def test_a_plain_confirmed_order_is_waiting_on_the_owner(self):
		self.assertEqual(describe_state(make_order())["key"], "to_fulfil")

	def test_the_label_is_the_owner_facing_wording_for_the_key(self):
		state = describe_state(make_order())
		self.assertEqual(state["label"], STAGE_LABELS["to_fulfil"])

	def test_a_cancelled_order_outranks_every_other_rung(self):
		lifecycle = frappe._dict(has_return=True, stage_from_shipment="delivered")
		state = describe_state(make_order(docstatus=2, per_delivered=100), lifecycle)
		self.assertEqual(state["key"], "cancelled")

	def test_a_draft_delivery_note_reads_as_drafted_not_as_waiting(self):
		lifecycle = frappe._dict(has_draft_delivery_note=True)
		self.assertEqual(describe_state(make_order(), lifecycle)["key"], "delivery_note_drafted")

	def test_a_packing_slip_advances_a_drafted_delivery_note_to_packed(self):
		lifecycle = frappe._dict(has_draft_delivery_note=True, has_packing_slip=True)
		self.assertEqual(describe_state(make_order(), lifecycle)["key"], "packed")

	def test_packing_never_outranks_fulfilment(self):
		"""ERPNext only allows a Packing Slip against a draft Delivery Note, so the slip that is
		still linked once that note is submitted must not drag a shipped order back to "Packed"."""
		lifecycle = frappe._dict(has_packing_slip=True)
		order = make_order(status="Completed", per_delivered=100)
		self.assertEqual(describe_state(order, lifecycle)["key"], "fulfilled")

	def test_a_part_shipped_order_is_partly_fulfilled(self):
		self.assertEqual(describe_state(make_order(per_delivered=40))["key"], "partly_fulfilled")

	def test_the_carrier_status_outranks_the_paperwork(self):
		lifecycle = frappe._dict(stage_from_shipment="delivered", has_packing_slip=True)
		order = make_order(status="Completed", per_delivered=100)
		self.assertEqual(describe_state(order, lifecycle)["key"], "delivered")

	def test_a_return_outranks_the_fulfilment_it_reverses(self):
		lifecycle = frappe._dict(has_return=True)
		order = make_order(status="Completed", per_delivered=100)
		self.assertEqual(describe_state(order, lifecycle)["key"], "returned")

	def test_a_status_the_ladder_has_no_rung_for_keeps_erpnexts_own_word(self):
		state = describe_state(make_order(status="On Hold"))
		self.assertEqual(state, {"key": "On Hold", "label": "On Hold"})



class TestAddressLines(UnitTestCase):
	"""ERPNext hands over address_display as HTML; the dashboard renders text, so the <br> tags
	used to appear literally on the order screen."""

	def test_break_tags_become_newlines(self):
		self.assertEqual(
			get_address_lines("12 King Fahd Road<br>Near Mall<br>Riyadh"),
			"12 King Fahd Road\nNear Mall\nRiyadh",
		)

	def test_the_self_closing_and_uppercase_spellings_break_too(self):
		self.assertEqual(get_address_lines("A<br/>B<BR />C"), "A\nB\nC")

	def test_surrounding_markup_is_stripped_rather_than_shown(self):
		self.assertEqual(get_address_lines("<div>Riyadh</div><br><span>SA</span>"), "Riyadh\nSA")

	def test_blank_segments_do_not_become_empty_lines(self):
		self.assertEqual(get_address_lines("Riyadh<br><br>   <br>SA"), "Riyadh\nSA")

	def test_an_address_with_nothing_in_it_reads_as_absent(self):
		for empty in (None, "", "<br><br>"):
			self.assertIsNone(get_address_lines(empty))


class TestOrderLifecycleReader(IntegrationTestCase):
	def test_no_orders_costs_no_queries(self):
		self.assertEqual(read_order_lifecycles([]), {})

	def test_an_autoincrement_named_order_is_keyed_as_a_string(self):
		"""A Sales Order named by autoincrement arrives as an int, and the caller looks it up
		with cstr(name) - the two have to meet on the same key or every badge falls back."""
		self.assertEqual(list(read_order_lifecycles([41])), ["41"])

	def test_an_order_with_no_paperwork_reads_back_empty(self):
		order = frappe.get_all("Sales Order", filters={"docstatus": 1}, limit=1, pluck="name")
		if not order:
			self.skipTest("no submitted Sales Order on this site")

		lifecycle = read_order_lifecycles(order)[order[0]]
		self.assertIsInstance(lifecycle.delivery_notes, list)

	def test_a_page_of_orders_costs_the_same_reads_as_a_single_one(self):
		"""The whole point of the reader: the badge column must not scale with the page size."""
		orders = frappe.get_all("Sales Order", limit=5, pluck="name")
		if len(orders) < 2:
			self.skipTest("needs at least two Sales Orders on this site")

		# Warm the doctype meta first: the very first read of a doctype in a process pays for its
		# schema, which would otherwise be counted against whichever page happened to run first.
		read_order_lifecycles(orders)

		one_order_queries = count_queries(orders[:1])
		self.assertEqual(count_queries(orders), one_order_queries)


def count_queries(order_names: list) -> int:
	calls = []
	original_sql = frappe.db.sql

	def counting_sql(query, *args, **kwargs):
		calls.append(query)
		return original_sql(query, *args, **kwargs)

	frappe.db.sql = counting_sql
	try:
		read_order_lifecycles(order_names)
	finally:
		frappe.db.sql = original_sql
	return len(calls)
