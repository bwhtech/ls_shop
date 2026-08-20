# Copyright (c) 2026, company@bwhstudios.com and contributors
# For license information, please see license.txt

"""The store dashboard's view of the storefront menu.

The menu manager itself lives with the doctype, in
`lifestyle_shop_ecommerce/doctype/lifestyle_settings/navbar/navbar_manager.py`, and the Desk
editor calls it there. This module is the seam the dashboard calls instead, so the SPA is not
wired to a doctype-internal module path.

Every mutation below returns the whole menu tree, so the editor replaces its state from the
response rather than patching a local copy and hoping the two agree.
"""

import frappe

from ls_shop.lifestyle_shop_ecommerce.doctype.ecommerce_category.ecommerce_category import (
	MAX_MENU_DEPTH,
)
from ls_shop.lifestyle_shop_ecommerce.doctype.lifestyle_settings.navbar import navbar_manager

# Re-exported by reference, not wrapped. `frappe.whitelist` records the function object, so the
# permission and allowed-method checks travel with it and a delegating wrapper would only add a
# stack frame. Renaming one of these is a breaking change for the dashboard, not a local edit.
add_node = navbar_manager.add_node
update_node = navbar_manager.update_node
delete_node = navbar_manager.delete_node
delete_all_nodes = navbar_manager.delete_all_nodes
get_delete_preview = navbar_manager.get_delete_preview
get_delete_all_preview = navbar_manager.get_delete_all_preview
move_node = navbar_manager.move_node
import_from_item_group = navbar_manager.import_from_item_group
set_visibility = navbar_manager.set_visibility
get_cascade_products = navbar_manager.get_cascade_products
get_publish_preview = navbar_manager.get_publish_preview
set_published = navbar_manager.set_published


@frappe.whitelist()
def get_editor_data():
	"""The menu, plus the two facts the editor would otherwise hardcode.

	`max_depth` lets the tree refuse a drop the server would reject anyway, and keeps the limit
	in one place when it changes.
	"""
	frappe.has_permission("Ecommerce Category", "read", throw=True)

	return {
		**navbar_manager.get_menu_editor_data(),
		"max_depth": MAX_MENU_DEPTH,
	}
