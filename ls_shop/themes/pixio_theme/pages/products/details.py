# The data layer is not duplicated: reusing www.products.details.get_context keeps SEO, stock,
# pricing and variant shapes identical between the themed and un-themed product page.
from ls_shop.www.products import details


def get_context(context):
	details.get_context(context)
	return context
