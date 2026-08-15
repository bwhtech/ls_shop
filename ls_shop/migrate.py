import traceback

import frappe

from ls_shop.search.build import ensure_index_built
from ls_shop.search.record_builder import DEFAULT_CONTENT_FIELDS
from ls_shop.search.result_card import DEFAULT_RESULT_FIELDS, RESULT_CARD_CATALOG
from ls_shop.www.llms import DEFAULT_LLMS_TXT

# Marks the robots.txt value as ours. Its absence from a non-blank value means an admin
# has taken the file over by hand, and we leave it alone from then on.
ROBOTS_MARKER = "# managed by ls_shop"


def after_install():
	create_payment_modes()
	try:
		create_default_email_templates()
	except Exception as e:
		import traceback

		error_msg = f"Error creating default email templates: {e!s}"
		frappe.log_error(traceback.format_exc(), "Lifestyle Shop Installation - Email Templates")
		frappe.errprint(error_msg)
		frappe.errprint(traceback.format_exc())

	register_optional_doctype_links()
	populate_search_settings()
	ensure_storefront_search_index()
	setup_robots_txt()
	seed_llms_txt()


def after_migrate():
	register_optional_doctype_links()
	populate_search_settings()
	ensure_storefront_search_index()
	setup_robots_txt()
	seed_llms_txt()


def populate_search_settings():
	"""Seed the search content/result field tables when they have never been configured (idempotent)."""
	if not frappe.db.exists("DocType", "Lifestyle Settings"):
		return

	settings = frappe.get_single("Lifestyle Settings")
	if settings.search_content_fields and settings.search_result_fields:
		return

	if not settings.search_content_fields:
		for search_doctype, field in DEFAULT_CONTENT_FIELDS:
			settings.append("search_content_fields", {"search_doctype": search_doctype, "field": field})

	if not settings.search_result_fields:
		for field in RESULT_CARD_CATALOG:
			settings.append(
				"search_result_fields",
				{"field": field, "show": 1 if field in DEFAULT_RESULT_FIELDS else 0},
			)

	# Fresh site: company/price lists are unset, so ignore_mandatory stops save() raising MandatoryError.
	settings.flags.ignore_mandatory = True
	settings.save(ignore_permissions=True)


def ensure_storefront_search_index():
	"""Backstop the storefront search index on install/migrate; never fail migrate over it."""
	try:
		ensure_index_built()
	except Exception:
		frappe.log_error(traceback.format_exc(), "Storefront Search Index - ensure_index_built")


def register_optional_doctype_links():
	"""Add Customize Form connections for optional integrations whose doctypes are
	provided by tabby_frappe.
	"""
	add_sales_order_link_if_doctype_exists("Tabby Payment Request", "ref_docname")


def add_sales_order_link_if_doctype_exists(link_doctype: str, link_fieldname: str):
	if not frappe.db.exists("DocType", link_doctype):
		return

	customize_form = frappe.get_doc({"doctype": "Customize Form", "doc_type": "Sales Order"})
	customize_form.run_method("fetch_to_customize")
	if any(row.link_doctype == link_doctype for row in (customize_form.get("links") or [])):
		return

	customize_form.append(
		"links",
		{
			"link_doctype": link_doctype,
			"link_fieldname": link_fieldname,
		},
	)
	try:
		customize_form.save()
	except Exception:
		import traceback

		frappe.log_error(traceback.format_exc(), f"ls_shop: optional link for {link_doctype}")


def create_payment_modes():
	modes = {"Telr"}

	for mode in modes:
		frappe.get_doc(
			{
				"doctype": "Mode of Payment",
				"mode_of_payment": mode,
				"enabled": True,
				"type": "Bank",
			}
		).insert(ignore_if_duplicate=True)


def create_default_email_templates():
	"""Create default email templates required by Lifestyle Settings"""

	email_templates = [
		{
			"name": "Order Confirmation",
			"subject": "Order Confirmation - {{ doc.name }}",
			"response": """Dear {{ doc.customer_name }},

Thank you for your order! Your order has been confirmed.

Order Details:
Order ID: {{ doc.name }}
Date: {{ doc.transaction_date }}
Total: {{ doc.grand_total }}

You can track your order status at: {{ login_url }}

Best regards,
{{ company }}""",
			"doctype": "Sales Order",
		},
		{
			"name": "Item In Stock",
			"subject": "Item Back in Stock - {{ item.item_name }}",
			"response": """Dear Customer,

Great news! The item "{{ item.item_name }}" is now back in stock.

You can purchase it now at: {{ item_url }}

Best regards,
{{ company }}""",
			"doctype": "Item",
		},
		{
			"name": "Order Cancellation",
			"subject": "Order Cancellation Confirmation - {{ doc.name }}",
			"response": """Dear {{ doc.customer_name }},

Your order {{ doc.name }} has been cancelled as requested.

If you have any questions, please contact our customer service.

Best regards,
{{ company }}""",
			"doctype": "Sales Order",
		},
	]

	for template_data in email_templates:
		if not frappe.db.exists("Email Template", template_data["name"]):
			template = frappe.get_doc({"doctype": "Email Template", **template_data})
			template.insert(ignore_permissions=True)
			frappe.errprint(f"Created Email Template: {template_data['name']}")
		else:
			frappe.errprint(f"Email Template '{template_data['name']}' already exists")


def seed_llms_txt():
	# Seed rather than serve-only, so admins get an editable starting point instead of a
	# page they can only replace wholesale.
	current = frappe.db.get_single_value("Lifestyle Settings", "llms_txt")
	if not (current and current.strip()):
		frappe.db.set_single_value("Lifestyle Settings", "llms_txt", DEFAULT_LLMS_TXT)


def setup_robots_txt():
	# Core's frappe/www/robots.py serves this value, so we only write it.
	current = frappe.db.get_single_value("Website Settings", "robots_txt") or ""
	if current.strip() and ROBOTS_MARKER not in current:
		return

	site_url = frappe.utils.get_url().rstrip("/")
	robots_txt = (
		f"{ROBOTS_MARKER}\n"
		"User-agent: *\n"
		"Allow: /\n"
		"Disallow: /app\n"
		"Disallow: /api\n"
		"Disallow: /private\n"
		# Faceted/sorted/paged listings are duplicate surfaces of the same catalogue; they
		# burn crawl budget and dilute signals.
		"Disallow: /*?search=\n"
		"Disallow: /*?sort=\n"
		"Disallow: /*?page=\n"
		"Disallow: /*?filter=\n"
		# Disallow is a prefix match, so "/en/cart" already covers "/en/cart/checkout".
		# The explicit checkout line is kept deliberately — do not "tidy" these away.
		"Disallow: /en/cart\n"
		"Disallow: /ar/cart\n"
		"Disallow: /en/cart/checkout\n"
		"Disallow: /en/account\n"
		"Disallow: /ar/account\n\n"
		f"Sitemap: {site_url}/sitemap.xml\n"
	)
	frappe.db.set_single_value("Website Settings", "robots_txt", robots_txt)
