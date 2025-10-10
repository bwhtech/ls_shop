"""
Quick script to publish all demo items to the website
Run this if products don't show on the website after running install_demo_data
"""

import frappe


def publish_all_demo_items():
	"""Publish all demo product items to website"""

	print("Publishing demo items to website...")

	# Get warehouse
	warehouse = frappe.db.get_value("Warehouse", {"is_group": 0}, "name")
	if not warehouse:
		print("❌ No warehouse found")
		return

	# Get all items
	items = frappe.get_all(
		"Item",
		filters={"has_variants": 0, "is_stock_item": 1},
		fields=["name", "item_name", "item_group", "brand", "description"],
	)

	created = 0
	published = 0

	for item in items:
		wi_name = frappe.db.get_value("Website Item", {"item_code": item.name}, "name")

		if not wi_name:
			# Create Website Item
			wi = frappe.get_doc(
				{
					"doctype": "Website Item",
					"item_code": item.name,
					"item_name": item.item_name,
					"web_item_name": item.item_name,
					"item_group": item.item_group,
					"brand": item.brand or "",
					"description": item.description or "",
					"website_warehouse": warehouse,
					"published": 1,
					"website_item_groups": [{"item_group": item.item_group}] if item.item_group else [],
				}
			)
			wi.insert(ignore_permissions=True)
			created += 1
		else:
			# Update existing
			frappe.db.set_value("Website Item", wi_name, {"published": 1, "website_warehouse": warehouse})

			# Ensure website_item_groups is set
			wi = frappe.get_doc("Website Item", wi_name)
			if not wi.website_item_groups and item.item_group:
				wi.append("website_item_groups", {"item_group": item.item_group})
				wi.save(ignore_permissions=True)

			published += 1

	# Fix Style Attribute Variant routes (remove language prefix)
	savs = frappe.get_all("Style Attribute Variant", fields=["name", "route"])
	sav_fixed = 0

	for sav in savs:
		if sav.route:
			# Remove any language/products prefix
			clean_route = sav.route.replace("en/products/", "").replace("ar/products/", "")
			if clean_route != sav.route:
				frappe.db.set_value("Style Attribute Variant", sav.name, "route", clean_route)
				sav_fixed += 1

	# Publish all SAVs that have sizes
	sav_published = 0
	all_savs = frappe.get_all("Style Attribute Variant", fields=["name"])
	for sav in all_savs:
		has_sizes = frappe.db.exists("Color Size Item", {"parent": sav.name})
		if has_sizes:
			frappe.db.set_value("Style Attribute Variant", sav.name, "is_published", 1)
			sav_published += 1

	# Fix Website Item routes (should be simple slug without prefix)
	website_items = frappe.get_all("Website Item", fields=["name", "item_code", "route"])
	routed = 0

	for wi in website_items:
		# Generate clean route (just the slug)
		item_code = wi.item_code.lower().replace("_", "-").replace(" ", "-")

		# Remove any existing prefix and ensure it's just the slug
		if wi.route:
			clean_route = wi.route.replace("en/products/", "").replace("ar/products/", "")
			if clean_route != item_code:
				frappe.db.set_value("Website Item", wi.name, "route", item_code)
				routed += 1
		else:
			frappe.db.set_value("Website Item", wi.name, "route", item_code)
			routed += 1
	# nosemgrep: manual commit required for demo item publishing completion
	frappe.db.commit()
	frappe.clear_cache()

	print("\n✅ Complete!")
	print(f"   Created: {created} Website Items")
	print(f"   Published: {published} existing items")
	print(f"   Fixed SAV routes: {sav_fixed}")
	print(f"   Published SAVs: {sav_published}")
	print(f"   Fixed Website Item routes: {routed}")
	print("\nVisit: https://your-site.com/en/products")
	print("\nNote: Routes should be clean slugs (e.g., 'tshirt-classic-black')")
	print("      The /en/products/ prefix is added by hooks.py routing")


if __name__ == "__main__":
	publish_all_demo_items()
