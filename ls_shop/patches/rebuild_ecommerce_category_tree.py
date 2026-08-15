import frappe
from frappe.utils.nestedset import rebuild_tree


def execute():
	"""Seat pre-tree Ecommerce Category rows in the nested set.

	`bench migrate` adds the lft/rgt columns but never populates them, so every row that predates
	the tree lands at 0/0. Left there, `update_add_node` reads a max(rgt) of 0 and hands the next
	insert a band that overlaps them, and deleting one walks a bogus band — so the rebuild has to
	happen once, on migrate, not by hand.
	"""
	if not frappe.db.exists("Ecommerce Category", {"rgt": 0}):
		return

	rebuild_tree("Ecommerce Category")
