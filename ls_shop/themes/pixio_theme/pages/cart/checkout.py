# The data layer is not duplicated: reusing www.cart.checkout.get_context keeps the quotation,
# addresses, payment modes and delivery configuration identical between the themed and
# un-themed checkout - including the guest PermissionError and the empty-cart redirect.
from ls_shop.www.cart import checkout


def get_context(context):
	checkout.get_context(context)
	return context
