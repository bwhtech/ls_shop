# The data layer is not duplicated: reusing www.index.get_context keeps SEO, search shapes
# and product data identical between the themed and un-themed home page.
from ls_shop.www import index


def get_context(context):
	index.get_context(context)
	return context
