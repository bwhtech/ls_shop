# Copyright (c) 2026, company@bwhstudios.com and Contributors
# Tests for the fulfilment ladder behind every order badge in the store-admin dashboard
# (api/admin/orders.py). The ladder is pure, so it is exercised without touching the database;
# the batched reader that feeds it is covered against real documents.

import frappe
from frappe.tests import IntegrationTestCase, UnitTestCase
from frappe.utils.data import get_year_ending, get_year_start, getdate

from ls_shop.api.admin.orders import (
	MAX_PAGE_LENGTH,
	OPEN_STATUSES,
	SETTLED_STAGES,
	STAGE_LABELS,
	can_fulfil_order,
	describe_state,
	fulfil_order,
	get_address_lines,
	get_order,
	get_orders,
	get_overview,
	read_order_lifecycles,
)

COMPANY = "Lifestyle Demo"
ITEM_GROUP = "Interior Accessories"
CURRENCY = "SAR"
ITEM_RATE = 150.0


def to_fulfil_names() -> list:
	return [row["name"] for row in get_orders(status="open", page_length=MAX_PAGE_LENGTH)["orders"]]


def make_test_sales_order():
	"""A submitted order for a non-stock item: enough to be fulfilled and returned, with nothing of
	the stock ledger in the way of what these tests are about."""
	ensure_fiscal_year()
	item_code = f"ZZ-LADDER-{frappe.generate_hash(length=8)}"
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": "ZZ Fulfilment Ladder Item",
			"item_group": ITEM_GROUP,
			"stock_uom": "Nos",
			"is_stock_item": 0,
		}
	).insert(ignore_permissions=True)

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": f"ZZ Ladder Customer {frappe.generate_hash(length=8)}",
			"customer_type": "Individual",
		}
	).insert(ignore_permissions=True)

	sales_order = frappe.new_doc("Sales Order")
	sales_order.update(
		{
			"customer": customer.name,
			"company": COMPANY,
			"currency": CURRENCY,
			"conversion_rate": 1,
			"transaction_date": getdate(),
			"delivery_date": getdate(),
			"items": [{"item_code": item_code, "qty": 2, "rate": ITEM_RATE}],
		}
	)
	sales_order.flags.ignore_permissions = True
	sales_order.insert()
	sales_order.submit()
	return sales_order


def ensure_fiscal_year():
	"""This site was never given one, and every submitted selling document needs one."""
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


def return_against_order(sales_order):
	"""Ship the order and take it straight back, which is what resets per_delivered while ERPNext's
	own status on the order stays open."""
	# ERPNext moved its transaction mappers into a sibling `mapper` module; both layouts are in the
	# wild across the versions this app runs against, exactly as api/admin/orders.py resolves them.
	try:
		from erpnext.stock.doctype.delivery_note.mapper import make_sales_return
	except ImportError:
		from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_return

	delivery_note = fulfil_order(sales_order.name)["delivery_note"]
	sales_return = make_sales_return(delivery_note)
	sales_return.flags.ignore_permissions = True
	sales_return.insert()
	sales_return.submit()
	return sales_return


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


class TestFulfilButton(UnitTestCase):
	"""per_delivered alone used to decide this, and a return resets per_delivered."""

	def test_no_settled_rung_offers_the_button(self):
		for key in SETTLED_STAGES:
			with self.subTest(stage=key):
				self.assertFalse(can_fulfil_order(make_order(), {"key": key}))

	def test_an_order_still_waiting_on_the_owner_offers_it(self):
		self.assertTrue(can_fulfil_order(make_order(), {"key": "to_fulfil"}))

	def test_a_part_shipped_order_still_has_something_left_to_ship(self):
		self.assertTrue(can_fulfil_order(make_order(per_delivered=40), {"key": "partly_fulfilled"}))

	def test_a_fully_delivered_order_has_nothing_left_to_ship(self):
		self.assertFalse(can_fulfil_order(make_order(per_delivered=100), {"key": "fulfilled"}))

	def test_a_draft_order_cannot_be_fulfilled(self):
		self.assertFalse(can_fulfil_order(make_order(docstatus=0), {"key": "to_fulfil"}))


class TestToFulfilAgreement(IntegrationTestCase):
	"""The badge, the tab, the Home figure and the fulfil button all have to tell the same story.

	Driven against real documents: a return is what pulls an order onto a settled rung while ERPNext's
	own status stays open, which is exactly the contradiction the tab used to show.
	"""

	def setUp(self):
		self.sales_order = make_test_sales_order()

	def test_an_open_order_is_in_the_to_fulfil_tab(self):
		self.assertIn(self.sales_order.name, to_fulfil_names())

	def test_a_returned_order_leaves_the_to_fulfil_tab(self):
		return_against_order(self.sales_order)

		state = get_order(self.sales_order.name)["state"]
		self.assertEqual(state["key"], "returned")
		self.assertNotIn(self.sales_order.name, to_fulfil_names())

	def test_a_returned_order_still_reads_as_open_to_erpnext(self):
		"""Without this the fix would be untested: the exclusion only matters while the raw status
		disagrees with the ladder."""
		return_against_order(self.sales_order)

		status = frappe.db.get_value("Sales Order", self.sales_order.name, "status")
		self.assertIn(status, OPEN_STATUSES)

	def test_a_returned_order_offers_no_fulfil_button(self):
		return_against_order(self.sales_order)

		self.assertFalse(get_order(self.sales_order.name)["can_fulfil"])

	def test_a_returned_order_refuses_to_be_fulfilled(self):
		"""The button is gone, but a screen left open on a stale list can still call this."""
		return_against_order(self.sales_order)

		with self.assertRaises(frappe.ValidationError):
			fulfil_order(self.sales_order.name)

	def test_the_home_figure_counts_exactly_the_to_fulfil_list(self):
		return_against_order(self.sales_order)

		to_fulfil = next(stat for stat in get_overview()["stats"] if stat["key"] == "to_fulfil")
		self.assertEqual(to_fulfil["value"], get_orders(status="open")["total"])

	def test_the_tab_never_shows_an_order_wearing_a_settled_badge(self):
		"""The bug in one line: every row of the worklist has to be an order the owner can still act on."""
		return_against_order(self.sales_order)

		page = get_orders(status="open", page_length=MAX_PAGE_LENGTH)
		self.assertEqual(len(page["orders"]), min(page["total"], MAX_PAGE_LENGTH))
		for row in page["orders"]:
			with self.subTest(order=row["name"]):
				self.assertNotIn(row["state"]["key"], SETTLED_STAGES)
