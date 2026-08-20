# The data layer is not duplicated: reusing www.products.list.get_context keeps the facets, the
# SEO block and the product shape identical between the themed and un-themed listing.
from ls_shop.www.products import list as products_list


def get_context(context):
	products_list.get_context(context)
	return context
