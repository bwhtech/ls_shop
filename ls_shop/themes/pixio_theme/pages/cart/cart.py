# The data layer is not duplicated: reusing www.cart.cart.get_context keeps the delivery
# configuration and breadcrumbs identical between the themed and un-themed cart.
from ls_shop.www.cart import cart


def get_context(context):
	cart.get_context(context)
	return context
