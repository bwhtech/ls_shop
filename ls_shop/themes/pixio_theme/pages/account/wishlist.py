# The wishlist itself lives in the Alpine store, not the page context, so this controller only
# reuses the un-themed page's context rather than restating it.
from ls_shop.www.account import wishlist


def get_context(context):
	wishlist.get_context(context)
	return context
