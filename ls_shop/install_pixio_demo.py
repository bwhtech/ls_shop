"""One-shot seeder for a Pixio storefront demo site. install_demo_data.create_price_lists is skipped:
it hardcodes USD, which blocks every Sales Invoice on a site whose company is not USD."""

import frappe

from ls_shop.install_analytics_demo_data import install_analytics_demo_data
from ls_shop.install_demo_data import (
	configure_lifestyle_settings,
	create_item_attributes,
	ensure_warehouse_exists,
)
from ls_shop.install_fashion_demo_data import (
	DEFAULT_SIZES,
	FASHION_PRODUCTS,
	IMAGE_ROOT,
	install_fashion_demo_data,
)
from ls_shop.install_pixio_theme_data import PRODUCTS_URL, install_pixio_theme_data

THEME = "Pixio Theme"
DEMO_SIZES = DEFAULT_SIZES
SALE_PRICE_LIST = "Sale Price List"
SHIPPING_RULE = "Standard Shipping"

# Rupee-scale money; install_demo_data's own numbers read as dollars and free-ship every demo cart.
FREE_SHIPPING_ABOVE = 999
FLAT_SHIPPING_CHARGE = 99
COD_CHARGE = 49
COD_CHARGE_APPLICABLE_BELOW = 999

# Rates are recomputed from FASHION_PRODUCTS, never scaled in place — a re-run would compound.
RUPEE_MULTIPLIER = 50

DEFAULT_HOMEPAGE_IMAGES = "/assets/ls_shop/images/homepage/demo"
DEFAULT_HERO_BANNERS = ("hero-1.webp", "hero-2.webp", "hero-3.webp", "hero-4.webp")
DEFAULT_PROMO_TILES = ("tile-1.webp", "tile-2.webp", "tile-3.webp", "tile-4.webp")
DEFAULT_WIDE_BANNER = "wide-1.webp"

STORE_COPY = {
	"store_name": "Pixio",
	"brand_logo": f"{IMAGE_ROOT}/logo.svg",
	"footer_logo": f"{IMAGE_ROOT}/logo-white.svg",
	"contact_phone": "+91 98765 43210",
	"contact_email": "hello@pixio.demo",
	"working_hours": "Mon - Sat, 10:00 - 19:00",
	"newsletter_title": "Sign Up For Newsletter",
	"newsletter_description": "Get the latest drops and offers straight to your inbox.",
	# The template already renders "© {year}" ahead of this, so the symbol and year stay out of it.
	"copyright_text": "Pixio. All Rights Reserved.",
}

# Every URL must point at a route this storefront actually serves.
FOOTER_SECTIONS = (
	{
		"section_title": "Our Stores",
		"links": (
			"New York",
			"London SF",
			"Edinburgh",
			"Los Angeles",
			"Chicago",
			"Las Vegas",
		),
	},
	{
		"section_title": "Useful Links",
		"links": (
			("Privacy Policy", "/en/products"),
			("Returns", "/en/account/orders"),
			("Terms & Conditions", "/en/products"),
			("Contact Us", "/en/account/profile"),
			("Latest News", "/en/products"),
			("Our Sitemap", "/sitemap.xml"),
		),
	},
	{
		"section_title": "Footer Menu",
		"links": (
			("New Collection", "/en/products"),
			("Woman Dress", "/en/products"),
			("Contact Us", "/en/account/profile"),
			("Latest News", "/en/products"),
			("My Account", "/en/account/dashboard"),
		),
	},
)


def install_pixio_demo():
	"""Seed a demo storefront end to end. Safe to re-run."""
	configure_site_defaults()
	save_sale_price_list()
	create_item_attributes()
	normalise_size_attribute()
	save_shipping_rule()

	configure_lifestyle_settings()
	apply_store_copy()

	activate_pixio_theme()
	install_fashion_demo_data()
	apply_rupee_prices()
	install_pixio_theme_data()
	apply_rupee_hero_prices()

	save_default_homepage()
	save_footer_sections()
	save_mode_of_payment_accounts()

	seed_storefront_analytics()

	# nosemgrep: manual commit required, this runs outside a request
	frappe.db.commit()
	frappe.clear_cache()
	print("✅ Pixio demo seeded")


def seed_storefront_analytics():
	"""Give the analytics screen a store worth looking at."""
	# Must run after the catalogue: the events and orders it writes reference real item codes.
	install_analytics_demo_data()


def configure_site_defaults():
	"""The three site-level settings that silently break a paid checkout later."""
	# A blank System Settings.language crashes money_in_words (num2words(lang=None)) on every invoice;
	# a Contact whose email_id is not an address is rejected by the gateways.
	frappe.db.set_single_value("System Settings", "language", "en")
	frappe.db.set_single_value("System Settings", "country", "India")
	frappe.db.set_default("currency", "INR")

	contact = frappe.db.get_value("Contact", {"user": "Administrator"})
	if contact:
		frappe.db.set_value(
			"Contact", contact, "email_id", frappe.db.get_value("User", "Administrator", "email")
		)


def save_sale_price_list():
	"""Built here rather than through install_demo_data.create_price_lists, which pins USD."""
	if frappe.db.exists("Price List", SALE_PRICE_LIST):
		frappe.db.set_value("Price List", SALE_PRICE_LIST, "currency", get_company_currency())
		return

	frappe.get_doc(
		{
			"doctype": "Price List",
			"price_list_name": SALE_PRICE_LIST,
			"currency": get_company_currency(),
			"enabled": 1,
			"buying": 0,
			"selling": 1,
		}
	).insert(ignore_permissions=True)


def normalise_size_attribute():
	"""Replace ERPNext's Small/Medium/Large Size values with the demo's literal S/M/L/XL."""
	# ERPNext ships Size as Small/Medium/Large abbreviated S/M/L, so a literal "S" fails as invalid.
	attribute = frappe.get_doc("Item Attribute", "Size")
	existing = {row.attribute_value for row in attribute.item_attribute_values}
	if set(DEMO_SIZES).issubset(existing):
		return

	if frappe.db.exists("Item Variant Attribute", {"attribute": "Size"}):
		frappe.throw(
			frappe._("Size attribute is already used by item variants — reset it by hand before seeding.")
		)

	attribute.item_attribute_values = []
	for size in DEMO_SIZES:
		attribute.append("item_attribute_values", {"attribute_value": size, "abbr": size})

	attribute.save(ignore_permissions=True)


def save_shipping_rule():
	if frappe.db.exists("Shipping Rule", SHIPPING_RULE):
		return

	company = get_company()
	account = get_freight_account()
	cost_center = frappe.db.get_value("Cost Center", {"company": company, "is_group": 0}, "name")

	frappe.get_doc(
		{
			"doctype": "Shipping Rule",
			"label": SHIPPING_RULE,
			"shipping_rule_type": "Selling",
			"calculate_based_on": "Net Total",
			"company": company,
			"account": account,
			"cost_center": cost_center,
			"conditions": [
				{"from_value": 0, "to_value": FREE_SHIPPING_ABOVE, "shipping_amount": FLAT_SHIPPING_CHARGE},
				{"from_value": FREE_SHIPPING_ABOVE, "to_value": 9999999, "shipping_amount": 0},
			],
		}
	).insert(ignore_permissions=True)


def apply_store_copy():
	"""Rupee-scale COD thresholds and the storefront's own name, over what configure_lifestyle_settings left."""
	settings = frappe.get_doc("Lifestyle Settings")
	settings.cod_enabled = 1
	settings.cod_charge = COD_CHARGE
	settings.cod_charge_applicable_below = COD_CHARGE_APPLICABLE_BELOW
	settings.ecommerce_warehouse = ensure_warehouse_exists()
	# Without this, set_cod_charges throws "Please select a valid account for cod charges".
	settings.charge_account_head = get_freight_account()

	for fieldname, value in STORE_COPY.items():
		settings.set(fieldname, value)

	settings.save(ignore_permissions=True)


def apply_rupee_prices():
	"""Restate every catalogue price at rupee scale, rounded to a plausible retail number."""
	for product in FASHION_PRODUCTS:
		rates = {
			"Standard Selling": to_rupees(product["base_price"]),
			SALE_PRICE_LIST: to_rupees(product["sale_price"]),
		}
		for price_list, rate in rates.items():
			for name in frappe.get_all(
				"Item Price",
				filters={"item_code": ["like", f"{product['code']}-%"], "price_list": price_list},
				pluck="name",
			):
				frappe.db.set_value("Item Price", name, "price_list_rate", rate)


def to_rupees(amount):
	"""Dollar-scale amount as a rupee price ending in 99, the shape a shopper expects."""
	return round(amount * RUPEE_MULTIPLIER / 100) * 100 - 1


def apply_rupee_hero_prices():
	"""Restate the hero slides' dollar copy at the catalogue's rupee scale."""
	settings = frappe.get_doc("Pixio Theme Settings")
	for slide in settings.hero_slides:
		amount = "".join(
			character for character in (slide.subheading or "") if character.isdigit() or character == "."
		)
		if not amount:
			continue
		slide.subheading = f"₹{to_rupees(float(amount)):,}"

	settings.save(ignore_permissions=True)


def save_default_homepage():
	"""Fill Landing Page Settings so the un-themed storefront is a real page, not an empty one."""
	settings = frappe.get_doc("Landing Page Settings")

	settings.hero_banner = []
	for banner in DEFAULT_HERO_BANNERS:
		settings.append(
			"hero_banner",
			{"banner_image": f"{DEFAULT_HOMEPAGE_IMAGES}/{banner}", "url": PRODUCTS_URL},
		)

	for index, tile in enumerate(DEFAULT_PROMO_TILES, start=1):
		settings.set(f"gif_{index}", f"{DEFAULT_HOMEPAGE_IMAGES}/{tile}")
		settings.set(f"gif_url_{index}", PRODUCTS_URL)

	settings.banner_1 = f"{DEFAULT_HOMEPAGE_IMAGES}/{DEFAULT_WIDE_BANNER}"
	settings.banner_url_1 = PRODUCTS_URL

	published = frappe.get_all(
		"Style Attribute Variant", filters={"is_published": 1}, pluck="name", order_by="creation"
	)
	settings.new_arrivals = []
	settings.best_picks = []
	for name in published[:6]:
		settings.append("new_arrivals", {"item_variant": name})
	for name in published[6:12]:
		settings.append("best_picks", {"item_variant": name})

	settings.save(ignore_permissions=True)


def activate_pixio_theme():
	settings = frappe.get_doc("Shop Theme Settings")
	settings.active_theme = THEME
	settings.dynamic_pages_enabled = 1
	settings.save(ignore_permissions=True)


def save_footer_sections():
	"""Rebuild the footer from the reference columns, replacing whatever the base seeder left."""
	settings = frappe.get_doc("Lifestyle Settings")
	settings.footer_sections = []

	for section_order, section in enumerate(FOOTER_SECTIONS, start=1):
		title = section["section_title"]
		config = (
			frappe.get_doc("Footer Section Config", title)
			if frappe.db.exists("Footer Section Config", title)
			else frappe.new_doc("Footer Section Config")
		)
		config.section_title = title
		config.section_order = section_order
		config.enabled = 1
		config.footer_links = []

		for link_order, link in enumerate(section["links"], start=1):
			label, url = link if isinstance(link, tuple) else (link, "/en/products")
			config.append(
				"footer_links",
				{"link_label": label, "link_url": url, "link_order": link_order, "enabled": 1},
			)

		config.save(ignore_permissions=True)
		settings.append(
			"footer_sections",
			{"footer_section": config.name, "section_order": section_order, "enabled": 1},
		)

	settings.save(ignore_permissions=True)


def save_mode_of_payment_accounts():
	"""Give every Mode of Payment a company account row."""
	# Without one, create_payment_entry throws "Please set default Cash or Bank account in Mode of Payment".
	company = get_company()
	abbr = frappe.db.get_value("Company", company, "abbr")
	accounts = {
		"Cash": frappe.db.get_value("Account", {"company": company, "account_type": "Cash", "is_group": 0})
		or f"Cash - {abbr}",
		"Bank": frappe.db.get_value("Account", {"company": company, "account_type": "Bank", "is_group": 0})
		or f"Bank Account - {abbr}",
	}

	for mode_name in frappe.get_all("Mode of Payment", pluck="name"):
		mode = frappe.get_doc("Mode of Payment", mode_name)
		if any(row.company == company for row in mode.accounts):
			continue

		default_account = accounts.get(mode.type)
		if not default_account or not frappe.db.exists("Account", default_account):
			continue

		mode.append("accounts", {"company": company, "default_account": default_account})
		mode.save(ignore_permissions=True)


def get_freight_account():
	company = get_company()
	abbr = frappe.db.get_value("Company", company, "abbr")
	return (
		frappe.db.get_value(
			"Account", {"account_name": "Freight and Forwarding Charges", "company": company}, "name"
		)
		or f"Freight and Forwarding Charges - {abbr}"
	)


def get_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_value("Company", {}, "name")


def get_company_currency():
	return frappe.db.get_value("Company", get_company(), "default_currency") or "INR"
