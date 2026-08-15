import frappe
from frappe.utils import create_batch
from redis.exceptions import LockError

from ls_shop.search.build import ensure_index_built
from ls_shop.search.record_builder import IN_CLAUSE_CHUNK_SIZE
from ls_shop.search.sqlite_product_search import SqliteProductSearch

LOCK_KEY = "ls_shop_search_index_write"
LOCK_TIMEOUT = 30
LOCK_BLOCKING_TIMEOUT = 10


def on_update(doc, method=None):
	enqueue_upsert(doc.doctype, doc.name)


def after_rename(doc, method=None, old=None, new=None, merge=False):
	enqueue_upsert(doc.doctype, doc.name)


def on_trash(doc, method=None):
	enqueue_remove(doc.doctype, doc.name)


def skip_sync():
	"""Whether the per-doc sync events should stay quiet for this write."""
	return skip_batch_sync() or bool(frappe.flags.in_import)


def skip_batch_sync():
	"""Whether an explicitly requested batch sync should stay quiet for this write.

	Deliberately blind to `in_import`: a bulk importer sets that flag precisely so the per-doc events
	stop firing one job per row, then hands the whole set over once at the end. Honouring the flag here
	as well would swallow the replacement sync and leave the index stale until the nightly rebuild. The
	remaining flags all end in a full index build, so a batch job on top of them is pure waste.
	"""
	return bool(frappe.flags.in_migrate or frappe.flags.in_install or frappe.flags.in_patch)


def enqueue_upsert(doctype, name):
	if skip_sync():
		return
	frappe.enqueue(
		"ls_shop.search.sync.upsert_doc",
		queue="default",
		enqueue_after_commit=True,
		doctype=doctype,
		name=name,
	)


def enqueue_upsert_many(doctype, names):
	"""Re-sync a whole set of docs in one job.

	Bulk catalogue writes go through frappe.db.set_value, which never fires the document event that
	normally keeps the index fresh, so the caller has to hand the changed names over itself. One job
	rather than one per name: a bulk publish moves hundreds of products, and the batched engine write
	costs a single record build for all of them.

	Chunked because the names are serialised into the RQ payload: a bulk publish over a real catalogue
	is tens of thousands of names, which is a multi-megabyte job body for redis to carry.
	"""
	names = list(names)
	if skip_batch_sync() or not names:
		return
	for chunk in create_batch(names, IN_CLAUSE_CHUNK_SIZE):
		frappe.enqueue(
			"ls_shop.search.sync.upsert_docs",
			queue="long",
			enqueue_after_commit=True,
			doctype=doctype,
			names=chunk,
		)


def enqueue_remove(doctype, name):
	if skip_sync():
		return
	frappe.enqueue(
		"ls_shop.search.sync.remove_doc",
		queue="default",
		enqueue_after_commit=True,
		doctype=doctype,
		name=name,
	)


def upsert_doc(doctype, name):
	serialized_write(lambda engine: engine.index_doc(doctype, name))


def upsert_docs(doctype, names):
	if not SqliteProductSearch().index_exists():
		# First publish on a site that never had an index: there is nothing to patch, so fall through
		# to the normal first build instead of dropping the change on the floor until the nightly job.
		ensure_index_built()
		return
	serialized_write(lambda engine: engine.index_docs(doctype, names))


def remove_doc(doctype, name):
	serialized_write(lambda engine: engine.remove_doc(doctype, name))


def serialized_write(write):
	"""Run an index write under the single-writer cache lock; no-op until the index has been built."""
	engine = SqliteProductSearch()
	if not engine.index_exists():
		return
	try:
		with frappe.cache.lock(LOCK_KEY, timeout=LOCK_TIMEOUT, blocking_timeout=LOCK_BLOCKING_TIMEOUT):
			write(engine)
	except LockError:
		frappe.log_error(
			title="Search index sync lock timeout",
			message=(
				f"Could not acquire '{LOCK_KEY}' within {LOCK_BLOCKING_TIMEOUT}s; skipping this "
				"index write. The next nightly rebuild will reconcile it."
			),
		)
