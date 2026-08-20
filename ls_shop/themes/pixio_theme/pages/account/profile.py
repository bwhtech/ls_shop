# The data layer is not duplicated: www.account.profile.get_context already resolves the User
# doc and rejects guests, so the themed page reads exactly what the un-themed one reads.
from ls_shop.www.account import profile


def get_context(context):
	profile.get_context(context)
	return context
