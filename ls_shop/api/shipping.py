import frappe
from frappe import _
from frappe.utils.data import flt

from ls_shop.core import _get_cart_quotation
from ls_shop.utils import validate_document_access

# The Actual charge row the chosen delivery option posts through. Matched on description to find and
# replace the row on re-selection, the same way ERPNext's own shipping rule row is identified.
DELIVERY_CHARGE_DESCRIPTION = "Delivery Charges"

# ponytail: one notional box for the whole cart, since ls_shop has no parcel templates; swap for a
# Shipment Parcel Template on Lifestyle Settings once packing rules matter more than a rate estimate.
DEFAULT_PARCEL_DIMENSIONS = {"length": 30.0, "width": 20.0, "height": 10.0}
DEFAULT_ITEM_WEIGHT_KG = 0.5

RATES_CACHE_TTL_SECONDS = 30 * 60


def is_connector_installed() -> bool:
	"""bwh_shipping is a soft dependency: without it the storefront keeps the flat Shipping Rule."""
	return "bwh_shipping" in frappe.get_installed_apps()


@frappe.whitelist()
def get_shipping_options() -> dict:
	"""Delivery options priced for the cart's current shipping address.

	Never raises: checkout has to render even when the carrier is down. Each branch is reported so the
	storefront can say why the list is empty instead of showing a bare gap.
	"""
	quotation = _get_cart_quotation()
	if not quotation or not quotation.items:
		return {"options": []}
	if quotation.custom_is_store_pickup:
		return {"options": [], "store_pickup": True}
	if not is_connector_installed():
		return {"options": [], "connector_missing": True}
	if not quotation.shipping_address_name:
		return {"options": [], "address_missing": True}

	try:
		options = get_quoted_options(quotation)
	except Exception:
		# The connector itself failed — misconfigured, mid-upgrade, or a provider raising where it should
		# have degraded. Checkout still has to render, so it falls back to the flat Shipping Rule and the
		# storefront says the options are unavailable rather than showing an empty list as if there were
		# none.
		frappe.log_error(title="Shipping options could not be quoted")
		return {"options": [], "unavailable": True}

	return {"options": options, "selected": quotation.custom_delivery_option}


def get_quoted_options(quotation) -> list[dict]:
	"""Priced options for this cart, cached against a fingerprint of everything that changes the price.

	Cached because the storefront re-renders this block on every address edit, and each miss is a live
	carrier round trip. Anything that would change a quote — address, contents, value — is in the key, so
	a stale price cannot outlive what it was quoted for.
	"""
	cache_key = f"ls_shop:shipping_rates:{quotation.name}:{get_cart_fingerprint(quotation)}"
	cached = frappe.cache.get_value(cache_key)
	if cached is not None:
		return cached

	options = quote_options(quotation)
	frappe.cache.set_value(cache_key, options, expires_in_sec=RATES_CACHE_TTL_SECONDS)
	return options


def get_cart_fingerprint(quotation) -> str:
	items = ";".join(f"{item.item_code}x{flt(item.qty)}" for item in quotation.items)
	parts = (
		quotation.shipping_address_name or "",
		items,
		str(flt(quotation.net_total)),
		quotation.currency or "",
		get_services_stamp(),
	)
	return frappe.generate_hash("|".join(parts), 12)


def get_services_stamp() -> str:
	"""When the delivery options were last edited.

	In the fingerprint because the cart alone cannot see a change made in the desk: without it, an option
	disabled or repriced by an admin keeps being offered until every cached quote expires.
	"""
	latest = frappe.get_all("Shipping Service", fields=["modified"], order_by="modified desc", limit=1)
	return str(latest[0].modified) if latest else ""


def quote_options(quotation) -> list[dict]:
	"""Live-quote every enabled delivery option for this cart.

	No origin is passed: each provider ships from its own configured pickup address. Picking one origin for
	the whole store looks harmless until two providers ship from different countries, at which point the
	wrong one wins and every option silently drops to its backup charge.
	"""
	from bwh_shipping.bwh_shipping.pricing import quote_services
	from bwh_shipping.bwh_shipping.utils import get_address_payload

	return quote_services(
		None,
		get_address_payload(quotation.shipping_address_name),
		get_cart_parcels(quotation),
		get_cart_context(quotation),
		cod=False,
	)


def get_cart_context(quotation) -> dict:
	"""The figures the pricing engine needs to bracket a Shipping Rule band and convert its amount."""
	return {
		"currency": quotation.currency,
		"conversion_rate": flt(quotation.conversion_rate) or 1.0,
		"base_net_total": flt(quotation.base_net_total),
		"net_total": flt(quotation.net_total),
		"weight": get_cart_weight(quotation),
		"declared_value": flt(quotation.net_total),
	}


def get_cart_weight(quotation) -> float:
	"""Total cart weight in kg, from each item's own weight where ERPNext knows it.

	Read in one query rather than per line: this runs on every checkout render, and a get_doc per item is
	the classic N+1 on a big cart.
	"""
	item_codes = list({item.item_code for item in quotation.items})
	if not item_codes:
		return 0.0

	weights = frappe.get_all(
		"Item",
		filters={"name": ("in", item_codes)},
		fields=["name", "weight_per_unit", "weight_uom"],
	)
	weight_by_item = {row.name: row for row in weights}

	total = 0.0
	for item in quotation.items:
		row = weight_by_item.get(item.item_code)
		unit_weight = to_kg(row) if row else 0.0
		total += abs(flt(item.qty)) * (unit_weight or DEFAULT_ITEM_WEIGHT_KG)
	return flt(total, 3)


def to_kg(item_row) -> float:
	"""An Item's weight in kg. An unconvertible UOM counts as unknown, so the default weight applies."""
	from bwh_shipping.units import WEIGHT_IN_KG

	unit = (item_row.weight_uom or "kg").strip().casefold()
	factor = WEIGHT_IN_KG.get(unit)
	if factor is None:
		return 0.0
	return flt(item_row.weight_per_unit) * factor


def get_cart_parcels(quotation) -> list[dict]:
	return [
		{
			**DEFAULT_PARCEL_DIMENSIONS,
			"weight": get_cart_weight(quotation) or DEFAULT_ITEM_WEIGHT_KG,
			"count": 1,
		}
	]


@frappe.whitelist()
def set_delivery_option(delivery_option: str | None = None) -> dict:
	"""Persist the customer's choice and reprice the delivery fee server-side.

	The price is taken from a fresh server-side quote, never from the request: a client that could name its
	own delivery charge could ship for nothing.
	"""
	from ls_shop.api.payments import validate_cart_is_not_in_checkout

	quotation = _get_cart_quotation()
	validate_cart_is_not_in_checkout(quotation.name)

	if not delivery_option:
		clear_delivery_option(quotation)
		quotation.save(ignore_permissions=True)
		return get_delivery_summary(quotation)

	if quotation.custom_is_store_pickup:
		frappe.throw(_("This order is a store pickup, so it has no delivery option."))
	if not is_connector_installed():
		frappe.throw(_("Delivery options are not available on this store."))

	option = find_option(quotation, delivery_option)
	apply_delivery_option(quotation, option)
	quotation.save(ignore_permissions=True)
	return get_delivery_summary(quotation)


def find_option(quotation, delivery_option: str) -> dict:
	for option in get_quoted_options(quotation):
		if option["title"] == delivery_option:
			return option
	frappe.throw(_("Delivery option {0} is not available for this address.").format(delivery_option))


def apply_delivery_option(quotation, option: dict):
	quotation.custom_delivery_option = option["title"]
	quotation.custom_delivery_charge = flt(option["amount"])
	quotation.custom_shipping_provider = option.get("provider")
	quotation.custom_shipping_service_code = option.get("service_code")
	set_delivery_charge_row(quotation, flt(option["amount"]), option["title"])


def clear_delivery_option(quotation):
	quotation.custom_delivery_option = None
	quotation.custom_delivery_charge = 0
	quotation.custom_shipping_provider = None
	quotation.custom_shipping_service_code = None
	remove_delivery_charge_row(quotation)
	quotation.calculate_taxes_and_totals()


def set_delivery_charge_row(quotation, amount: float, title: str):
	"""Replace the delivery fee with an Actual charge row for the chosen option.

	The flat Shipping Rule is dropped first, row and all. Clearing only the link would leave the tax row
	ERPNext already appended sitting in the table, and the customer would pay the rule's charge on top of
	the option they picked. The rule's row goes before the option's, so a store whose rule and option share
	one account still ends up with exactly one delivery line.
	"""
	remove_shipping_rule_row(quotation)
	quotation.shipping_rule = None
	remove_delivery_charge_row(quotation)

	if amount > 0:
		quotation.append(
			"taxes",
			{
				"doctype": "Sales Taxes and Charges",
				"description": f"{DELIVERY_CHARGE_DESCRIPTION} - {title}",
				"charge_type": "Actual",
				"account_head": get_charge_account(title),
				"tax_amount": amount,
				# ERPNext refuses an inclusive Actual charge outright, and a site-level default of 1 would
				# otherwise fail the shopper's checkout. Pinned, exactly as the COD charge row does.
				"included_in_print_rate": 0,
			},
		)

	quotation.calculate_taxes_and_totals()


def remove_delivery_charge_row(quotation):
	quotation.taxes = [
		row for row in quotation.taxes if not (row.description or "").startswith(DELIVERY_CHARGE_DESCRIPTION)
	]
	reindex_taxes(quotation)


def remove_shipping_rule_row(quotation):
	"""Drop the tax row ERPNext's Shipping Rule appended, identified the way ERPNext identifies it.

	`ShippingRule.add_shipping_rule_to_tax_table` finds its own row by matching charge_type, account_head
	and cost_center, so the same triple is what separates it from a genuine tax the store charges. Matching
	on the description instead would miss a renamed rule and would break as soon as the label is translated.
	"""
	if not quotation.shipping_rule:
		return

	rule = frappe.get_cached_value(
		"Shipping Rule", quotation.shipping_rule, ["account", "cost_center"], as_dict=True
	)
	if not rule:
		return

	quotation.taxes = [
		row
		for row in quotation.taxes
		if not (
			row.charge_type == "Actual"
			and row.account_head == rule.account
			and row.cost_center == rule.cost_center
		)
	]
	reindex_taxes(quotation)


def reindex_taxes(quotation):
	for index, row in enumerate(quotation.taxes, start=1):
		row.idx = index


def get_charge_account(title: str) -> str:
	"""The option's own Shipping Rule account when it has one, else the store's charge account head."""
	from bwh_shipping.bwh_shipping.pricing import get_charge_account as get_option_account

	account = get_option_account(title)
	if account:
		return account

	account = frappe.get_cached_value("Lifestyle Settings", "Lifestyle Settings", "charge_account_head")
	if not account:
		frappe.throw(_("Set a Charge Account Head in Lifestyle Settings before charging for delivery."))
	return account


def get_delivery_summary(quotation) -> dict:
	return {
		"delivery_option": quotation.custom_delivery_option,
		"delivery_charge": flt(quotation.custom_delivery_charge),
		"grand_total": flt(quotation.rounded_total) or flt(quotation.grand_total),
		"currency": quotation.currency,
	}


def reprice_selected_option(quotation) -> bool:
	"""Re-apply the stored delivery option to the cart, as it stands now.

	Called on the way into payment, so a cart edited after the option was chosen is billed the delivery
	price its final contents earn rather than the one quoted for an older basket. Returns whether an option
	was applied at all, so the caller can fall back to the flat Shipping Rule.
	"""
	if not (quotation.custom_delivery_option and is_connector_installed()):
		return False

	from bwh_shipping.bwh_shipping.pricing import get_charge_amount

	for option in get_quoted_options(quotation):
		if option["title"] == quotation.custom_delivery_option:
			apply_delivery_option(quotation, option)
			return True

	# The option is no longer quotable for this address — disabled mid-checkout, or the carrier dropped the
	# route. Fall back to what the option can still be priced at rather than losing the charge entirely.
	amount = get_charge_amount(
		quotation.custom_delivery_option,
		get_cart_context(quotation),
		quoted_amount=flt(quotation.custom_delivery_charge) or None,
	)
	apply_delivery_option(
		quotation,
		{
			"title": quotation.custom_delivery_option,
			"amount": amount,
			"provider": quotation.custom_shipping_provider,
			"service_code": quotation.custom_shipping_service_code,
		},
	)
	return True


def copy_delivery_option_to_order(quotation_name: str, sales_order) -> None:
	"""Carry the paid-for delivery choice onto the Sales Order, so fulfilment books that exact service."""
	choice = frappe.db.get_value(
		"Quotation",
		quotation_name,
		[
			"custom_delivery_option",
			"custom_delivery_charge",
			"custom_shipping_provider",
			"custom_shipping_service_code",
		],
		as_dict=True,
	)
	if not (choice and choice.custom_delivery_option):
		return

	sales_order.custom_delivery_option = choice.custom_delivery_option
	sales_order.custom_delivery_charge = flt(choice.custom_delivery_charge)
	sales_order.custom_shipping_provider = choice.custom_shipping_provider
	sales_order.custom_shipping_service_code = choice.custom_shipping_service_code


@frappe.whitelist()
def get_order_tracking(sales_order: str) -> dict:
	"""Customer-facing tracking for one of their own orders."""
	validate_document_access("Sales Order", sales_order)

	if not is_connector_installed():
		return {"has_tracking": False}

	shipment = frappe.get_all(
		"Shipping Request",
		filters={"ref_doctype": "Sales Order", "ref_docname": sales_order},
		fields=["name", "awb", "carrier", "status", "label_url"],
		order_by="creation desc",
		limit=1,
	)
	if not shipment or not shipment[0].awb:
		return {"has_tracking": False}

	request = shipment[0]
	events = frappe.get_all(
		"Shipping Tracking Event",
		filters={"parent": request.name, "parenttype": "Shipping Request"},
		fields=["timestamp", "status", "location", "message"],
		order_by="timestamp desc",
	)
	return {
		"has_tracking": True,
		"awb": request.awb,
		"carrier": request.carrier,
		"status": request.status,
		"events": events,
	}
