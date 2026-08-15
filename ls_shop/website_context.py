import re

import frappe

from ls_shop import seo

# Cart/account/login render per-user content and must never be indexed. They are handled
# here rather than in each controller so a new private route inherits the rule for free.
UTILITY_PATH_PATTERN = re.compile(r"^/(?:en|ar)/(cart|account|login)(?:/|$)")

UTILITY_PAGE_NAMES = {"cart": "Cart", "account": "My Account", "login": "Login"}


def update_website_context(context):
	request = getattr(frappe.local, "request", None)
	request_path = request.path if request else ""

	match = UTILITY_PATH_PATTERN.match(request_path)
	if not match:
		return

	context.no_cache = 1
	context.seo = seo.build_page_seo({"noindex": 1}, display_name=UTILITY_PAGE_NAMES[match.group(1)])
	context.json_ld = []
