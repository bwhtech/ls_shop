# Bench version fix — frappe/erpnext round_floats_in mismatch

## Rollback-to-this state (recorded before any change)

- apps/frappe: branch `version-16`, SHA `8d901c9fe68adc337f4c89590ab85b347c348120` ("Bumped to Version 16.13.0"), working tree clean.
- apps/erpnext: branch `version-16`, SHA `9312781dcd1bb7b0cf35d96b7c816013addfa28a`, working tree clean.

To roll back frappe:
  git -C /home/frappe/frappe-bench/apps/frappe checkout 8d901c9fe68adc337f4c89590ab85b347c348120
  (then re-run bench setup requirements / pip install -e / bench migrate as needed)

## Problem
erpnext v16.14.0's taxes_and_totals.py:174 calls
  self.doc.round_floats_in(item, do_not_round_fields=do_not_round_fields)
but frappe's Document.round_floats_in at the recorded SHA has no do_not_round_fields param.
Every Quotation/Sales Order/Sales Invoice insert fails with TypeError.

## Resolution (applied)

- Fetched `upstream/version-16` for apps/frappe; confirmed commit `01e7893046` ("feat: do not round fields") adds the missing `do_not_round_fields` param to `Document.round_floats_in`.
- That commit is included in the frappe `16.14.0` release tag commit `abd538347d` ("chore(release): Bumped to Version 16.14.0"), which matches erpnext's installed version (16.14.0). `HEAD` (16.13.0) was a direct ancestor of that commit, so a fast-forward-only merge was possible — no rebase/divergence.
- Ran: `git -C apps/frappe merge --ff-only abd538347d`
  - frappe: `8d901c9fe68adc337f4c89590ab85b347c348120` (16.13.0) → `abd538347d0143f6026e4af53ddcb34a30b19aa9` (16.14.0)
  - erpnext: unchanged, `9312781dcd1bb7b0cf35d96b7c816013addfa28a` (16.14.0)
- `./env/bin/pip install -q -e apps/frappe` — no errors.
- `bench --site dev.localhost migrate` — completed cleanly (only a benign "DocType Recommended Items does not exist" fixture-skip warning, no tracebacks/errors).
- `bench build --app frappe` — completed cleanly.

## Verification

Inserted and submitted a real Sales Order via a temp module (`ls_shop/bench_fix_test.py`, deleted after use):
`{"name": "SAL-ORD-2026-00002", "grand_total": 3399.0, "customer": "Bench Fix Test Customer", "item_code": "CHECKERED-SLIM-SHIRT-BLU-L"}`
Test Sales Order was cancelled + force-deleted, and the test Customer force-deleted afterward — site left clean.

Re-ran `ls_shop.install_pixio_demo.install_pixio_demo` with `{"currency": "INR"}` (idempotent) — succeeded, seeded 60 days of analytics: 34546 events, 13640 sessions, 303 orders, 15 prior-history orders, 15 draft quotations.

Final counts: Sales Order = 318, Customer = 300, Item = 81.

Nothing was rolled back.
