import os

import frappe
from frappe.rate_limiter import rate_limit

from ls_shop.search.sqlite_product_search import SqliteProductSearch

SEARCH_CLASS_PATH = "ls_shop.search.sqlite_product_search.SqliteProductSearch"
CORE_BUILD_INDEX = "frappe.search.sqlite_search.build_index"
BUILD_TIMEOUT = 2 * 60 * 60 + 10 * 60


def enqueue_full_rebuild(deduplicate=False):
	"""Enqueue a full rebuild on the long queue. Returns the enqueue payload.

	`deduplicate` is for callers that can fire repeatedly (a settings save), so a burst of edits
	queues one rebuild instead of one per save.
	"""
	return frappe.enqueue(
		CORE_BUILD_INDEX,
		queue="long",
		timeout=BUILD_TIMEOUT,
		job_id=SEARCH_CLASS_PATH if deduplicate else None,
		deduplicate=deduplicate,
		search_class_path=SEARCH_CLASS_PATH,
		force=True,
	)


@frappe.whitelist()
@rate_limit(limit=5, seconds=60 * 60)
def rebuild_index():
	"""Manual entry: enqueue a full rebuild, restricted to System Manager and rate-limited."""
	frappe.only_for("System Manager")
	return enqueue_full_rebuild()


def rebuild_index_nightly():
	"""Nightly reconciler: full rebuild for bulk/related edits that bypass the per-doc sync events."""
	return enqueue_full_rebuild()


def ensure_index_built():
	"""Build the index when it is absent, or resume a build that died part-way through.

	Core's build writes into a temp DB and swaps it over on completion, so a leftover temp DB is the
	only trace of an interrupted build. This app does not register the `sqlite_search` hook, so core's
	own resume (build_index_if_not_exists) never sees this index — without the temp-DB check a build
	that dies on a large catalogue would restart from zero on the nightly rebuild instead of resuming.
	"""
	engine = SqliteProductSearch()
	is_continuation = os.path.exists(engine._get_db_path(is_temp=True))
	if engine.index_exists() and not is_continuation:
		return None
	if not frappe.db.exists("Style Attribute Variant", {"is_published": 1}):
		return None
	return frappe.enqueue(
		CORE_BUILD_INDEX,
		queue="long",
		timeout=BUILD_TIMEOUT,
		job_id=f"{SEARCH_CLASS_PATH}_continuation" if is_continuation else SEARCH_CLASS_PATH,
		deduplicate=True,
		search_class_path=SEARCH_CLASS_PATH,
		force=is_continuation,
		is_continuation=is_continuation,
	)
