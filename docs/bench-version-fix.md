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
