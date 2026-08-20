# The guest guard and the country list come from ls_shop.www.account.address so the themed and
# un-themed address pages read the same data. Its two display-only lists are not enough here:
# the Pixio card edits an address in place, so the whole document is needed. get_address_docs is
# the read those display strings are already built from, and it scopes to the signed-in
# shopper's party.
from ls_shop.core import get_address_docs, get_party
from ls_shop.www.account import address

no_cache = True


def get_context(context):
	address.get_context(context)
	context.addresses = get_address_docs()

	# A new address has to name the party it belongs to: frappe only infers one from the
	# shopper's Contact links, and this shop links the party through Portal User instead.
	party = get_party()
	context.party_doctype = party.doctype
	context.party_name = party.name
	return context
