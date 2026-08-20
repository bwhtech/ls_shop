# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""The store dashboard's view of the storefront footer.

The footer editor itself lives with the doctype, in
`lifestyle_shop_ecommerce/doctype/lifestyle_settings/footer/footer_preview.py`, and the Desk
editor calls it there. This module is the seam the dashboard calls instead, so the SPA is not
wired to a doctype-internal module path.

Every mutation returns the whole editor payload, so the page replaces its state from the
response rather than patching a local copy and hoping the two agree.
"""

import frappe
from frappe.utils import cint

from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.footer import footer_preview

# Re-exported by reference, not wrapped. `frappe.whitelist` records the function object, so the
# permission and allowed-method checks travel with it and a delegating wrapper would only add a
# stack frame. The `footer_` prefix is dropped because the module path already says footer.
# Renaming one of these is a breaking change for the dashboard, not a local edit.
get_editor_data = footer_preview.get_footer_editor_data
add_section = footer_preview.add_footer_section
rename_section = footer_preview.rename_footer_section
delete_section = footer_preview.delete_footer_section
reorder_sections = footer_preview.reorder_footer_sections
add_link = footer_preview.add_footer_link
update_link = footer_preview.update_footer_link
delete_link = footer_preview.delete_footer_link
reorder_links = footer_preview.reorder_footer_links
move_link = footer_preview.move_footer_link


@frappe.whitelist(methods=["POST"])
def set_section_enabled(name: str, enabled: int):
	"""Show or hide a whole footer column without deleting it and its links.

	The Desk editor never grew this, so there is nothing to re-export - but `enabled` is on the
	mapping row already and `get_footer_editor_data` already returns it, so the storefront reads
	the flag whether or not an editor can write it.
	"""
	frappe.has_permission("Lifestyle Settings", "write", throw=True)

	settings = frappe.get_single("Lifestyle Settings")
	row = next((mapping for mapping in settings.footer_sections if mapping.footer_section == name), None)
	if not row:
		frappe.throw(frappe._("Footer section {0} is not part of this footer.").format(name))

	row.enabled = cint(enabled)
	settings.save()

	return footer_preview.get_footer_editor_data()


@frappe.whitelist(methods=["POST"])
def set_link_enabled(section_name: str, link_row_name: str, enabled: int):
	"""Show or hide a single link, the column it sits in staying as it is."""
	frappe.has_permission("Lifestyle Settings", "write", throw=True)

	section = frappe.get_doc("Footer Section Config", section_name)
	row = next((link_row for link_row in section.footer_links if link_row.name == link_row_name), None)
	if not row:
		frappe.throw(frappe._("Link not found in {0}.").format(section_name))

	row.enabled = cint(enabled)
	section.save()

	return footer_preview.get_footer_editor_data()
