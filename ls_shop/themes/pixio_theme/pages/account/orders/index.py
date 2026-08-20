# The data layer is not duplicated: www.account.orders.index.get_context already resolves the
# guest check, the page number and the paginated order rows, so the themed page only re-skins it.
no_cache = True

from ls_shop.www.account.orders import index


def get_context(context):
	index.get_context(context)
	return context
