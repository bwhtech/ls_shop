import frappe

# Nav data moved onto the Ecommerce Category tree, so these no longer back anything.
DROPPED_CUSTOM_FIELDS = (
	"Item Group-custom_display_on_website",
	"Item Group-custom_item_group_display_name",
	"Brand-custom_display_on_website",
)


def execute():
	"""Delete the Custom Fields the menu manager replaced.

	Fixture sync only upserts — dropping a field from the fixture JSON leaves the Custom Field doc
	behind, and `Item Group-custom_item_group_display_name` is mandatory, so every Item Group insert
	keeps failing until the doc itself goes.
	"""
	for name in DROPPED_CUSTOM_FIELDS:
		if frappe.db.exists("Custom Field", name):
			frappe.delete_doc("Custom Field", name, ignore_permissions=True)
