# Commera wiring — open questions for Rahul

## From section 1 (Products) — commit 6a12845

1. **The "Type" filter/column was swapped for "Collection".** Products.vue shipped with a
   product-type filter, but ls_shop has no product-type concept at all (confirmed in the wiring
   map). The agent substituted `Item Group` as "Collection". This is a change to a design you
   approved, so it needs your yes/no. Alternatives: drop the column entirely, or build a real
   Product Type doctype (see the Product Types screen, which has the same problem).

2. **The "Draft" status tab always renders empty.** ls_shop products are `disabled` 0/1 — there is
   no draft state. The tab was kept so the frozen layout is unchanged. Options: hide the tab, or
   add a real draft concept.

3. **Sorting only sorts the loaded page.** `get_products` paginates server-side but has no
   order_by, so clicking a column header re-orders just the current page, not the result set.
   This is a real defect, not a design question. Fix: push order_by into the endpoint.
   Deferred so section 1 stayed scoped — should be picked up in a polish pass.

## From section 2 (Product Detail / Variant Detail) — commit 50bb732

4. **Money semantics — please confirm.** `default_rate` is treated as the higher struck-through
   "compare at" reference and `sale_rate` as what the shopper actually pays. This was read off
   the existing `ls_shop/product_detail.py:get_discount_percent`, not guessed — but it is money
   math, so it gets your eyes before it ships.

5. **One control was ADDED, not just wired: a Published switch on VariantDetail.vue.** The
   "needs a photo" rule (`unpublish_if_incomplete_data`) had to be surfaced up front as a
   disabled switch with a reason, and no such control existed in the prototype to attach it to.
   This is the one place tonight where the frozen design gained an element. Say the word and it
   comes out.

6. **Controls left deliberately inert** (no backing data model, documented in-code):
   Product Types (schema absent entirely) · Vendor · Tags · per-product Cost · per-product SEO
   (SEO lives per variant, not per product) · adding a new option to an existing product ·
   bulk "set stock to X" (only additive receive exists) · zip-based bulk photo import ·
   Barcode (no field anywhere) · SKU (ERPNext-assigned, read-only, no rename endpoint) ·
   product-level Status select (read-only; Archive/Restore is the single write path, to avoid
   two conflicting writers).

## From section 3 (Collections / Attributes) — this commit

7. **`Collections.vue` manages `Item Group`, not `Ecommerce Category`.** Both exist in ls_shop;
   section 1's `catalog.get_collections` (the Products filter) already reads `Item Group`, so this
   section stayed consistent with that rather than introducing a second "collections" concept.
   `Ecommerce Category` (15 seeded) is what the storefront navigation actually reads
   (`navigation.py`/`navbar_manager`) — if collections and storefront nav are meant to be the same
   thing to the owner, that is a merge decision for you, not one made here.

8. **"Type" (smart/manual) and "Condition" on the Collections list are truthful, not wired.**
   ls_shop has no smart-collection rule engine, so every row now reads "manual" / "—" for real
   (previously these were mock-hardcoded per row). The badge and column stay because the frozen
   layout has them, but nothing currently varies them — building a rule engine is separate, larger
   work called out in the wiring map, not attempted here.

9. **Attributes "Edit" now opens a small dialog to append one value** (reusing the same
   `dialog.prompt` pattern "New attribute" already used) — this was the one addition to a
   previously-unwired control that seemed safe: it only appends, and is the one place
   `catalog.check_abbreviations_are_distinct` (new — see below) can actually fire in the UI.
   Renaming or deleting a value, or renaming the attribute itself, is still not wired: an
   abbreviation edit after variants already exist does not move their item codes, and the "Size"
   attribute must literally keep that name (`generate_variants()` depends on it). Both are
   dangerous enough to warrant their own confirmation-dialog design — a UI decision, not made here.

10. **`catalog.check_abbreviations_are_distinct` did not already exist** (the brief for this
    section assumed it did). It has been added as a small guard function used by the new
    `add_attribute_value` endpoint, reusing the same case-insensitive comparison ERPNext's own
    `Item Attribute.validate_duplication` already applies on save.

## Product Types — needs a product decision

`ProductTypes.vue` is still on mock data — confirmed (again) that ls_shop has no product-type data
model at all. `Style Attribute Configurator` only carries `item_template`, `item_attribute`,
`recommended_items`; nothing models an arbitrary per-category field schema (author/ISBN for a book,
material/fit for a shirt). Three realistic ways to close this, not picked between here:

- **Reuse `Item Group` as a second axis alongside Collections.** Cheapest — no new doctype — but it
  overloads one field for two different owner-facing concepts (a "Collection" and a "Type" become
  the same underlying record), and Item Group carries no per-type field schema, so the screen's
  "author/pages/language" style fields still could not be built on it.
- **A new lightweight `Product Type` doctype, linked from `Style Attribute Configurator`.** Matches
  the mock's actual shape (a type owns a field schema; a product picks one type) and lets typed
  fields live somewhere real, but it is new schema, new migration, and a second create-product path
  to keep in sync with `catalog.create_product`.
- **Drop the screen.** If the owner never actually needs typed per-category fields — Pixio Retail's
  81 seeded items don't use any — this is the lowest-risk option: remove Product Types from the nav
  rather than carry a half-built concept indefinitely.

## Pricing: cost and margin — needs a product decision

`Pricing.vue`'s Margin column (section 4, `inventory`/`adjustments`/`pricing`) is now inert by design —
confirmed again that ls_shop has no cost, margin, or profit field anywhere in the data model. The
mock's 55%-assumed-COGS margin was always a pure client-side fabrication, never a stored value.
Nothing here picks a source; these are the realistic options:

- **`Bin.valuation_rate`** — already computed by ERPNext from every stock receipt's landed cost, so
  it needs no new field or data entry. But it moves with the moving-average valuation method and can
  be zero or stale for an item that has never had a costed receipt (allow-zero-valuation receipts,
  used by `receive_stock` when no rate is given, leave it at 0) — margin would silently read as 100%
  for exactly the items an owner is least likely to have priced carefully.
- **`Item.last_purchase_rate`** — a single number per item, simple to read and explain to a
  merchant. But it is only ever set by a Purchase Order/Receipt, which this dashboard's own
  `receive_stock` flow does not create — so for most of this store's stock it would simply be unset,
  same blind spot as valuation_rate from a different angle.
- **A new explicit cost field on the variant or its sizes.** The only option that is actually true to
  what the owner paid rather than an ERPNext side-effect, and the only one that works uniformly
  whether stock arrived through a Purchase Order, a manual receipt, or a future channel. Costs the
  most: new field, migration, and a data-entry step nothing else in the app currently asks for.

## Order Detail — Refund and Cancel order

`OrderDetail.vue`'s "Refund" and "Cancel order" actions (moreActions dropdown) stay inert. Neither
is a missing-endpoint problem exactly — the storefront already has real machinery
(`ls_shop.api.orders.get_refund_status` / `make_refund_payment_entry` / `cancel_order`) — but
neither is safe to point the admin dashboard at as-is:

**Refund — blocked by a pre-existing lookup bug, not a product decision.** `get_refund_status` and
`make_refund_payment_entry` find an order's payment via `Payment Entry Reference` filtered on
`reference_doctype = "Sales Order"`. In this codebase a captured payment's Payment Entry Reference
always points at the *Sales Invoice* raised for the order instead (`payments.create_sales_invoice`
→ `get_payment_entry("Sales Invoice", ...)`; verified by building a real prepaid order, invoice and
payment end to end against a scratch record and reading the resulting `Payment Entry Reference` row —
`reference_doctype` was `"Sales Invoice"`, never `"Sales Order"`). So `get_refund_status` reports
`can_refund: False` for every order, paid or not — refunded or never-paid look identical to it. This
is a real bug in shared storefront code (`ls_shop/api/orders.py`), out of this section's two-screen
scope to fix, and wiring the admin Refund button to it now would look live but silently do nothing.
`ls_shop/api/admin/orders.py`'s own `describe_payment` (used for the payment badge) reads the correct
Sales Invoice-linked path instead, so the badge is trustworthy even though the action isn't yet.
Once `get_refund_status`/`make_refund_payment_entry` are fixed to walk `Sales Invoice Item.sales_order`
the same way, an admin `refund_order` wrapper (permission-gated on `Sales Order` write, since that
helper's storefront caller is owner-scoped) is a same-day addition — the plumbing was written and
verified during this section, then pulled because it could not be shipped working.

**Cancel order — genuinely a product decision, not wired.** `ls_shop.api.orders.cancel_order` is
owner-scoped (`validate_can_cancel` throws unless `order.owner == frappe.session.user`) — it is the
storefront's "the shopper cancelled their own order" flow, not an admin action, and it is silent
about whether staff-initiated cancellation should behave identically. Three ways to close this:

- **Reuse `cancel_order`'s body, swap the ownership gate for a permission check.** Cheapest, and
  keeps its accounting behaviour (auto-refund for non-COD, cancel-the-draft-then-cancel for a
  confirmation-pending COD order) — but that behaviour was designed for a shopper acting on their own
  order, not for a merchant working a support case, and inherits the Refund bug above for any
  non-COD order.
- **A separate, admin-only cancel with a mandatory reason and no automatic refund.** Matches how a
  merchant actually cancels an order in practice (there is usually a conversation with the customer
  first) and avoids money movement inside a single click — but it is new flow, not reused, and still
  needs the Refund bug fixed before "cancel now, refund later" is a complete story.
- **Leave cancellation to the ERP Desk.** "View in ERP" already exists on this screen. Lowest-risk,
  but it sends the owner out of the tool this section is meant to keep them inside.

## Section 7 — Home, search, analytics

**Dashboard's "Needs attention" dropped a row rather than fabricate one.** The old mock's fourth
item ("N payments pending — Bank transfer not yet reconciled") has no real counterpart:
`orders.describe_payment_state` reports every COD order — this shop's entire seeded book — as
"pending" until the courier collects cash at the door, so a live count would just read "how many
COD orders exist", not something actionable. Left out rather than wired to a number that would
always be large and never mean anything. The remaining three rows (orders to fulfil, low stock,
products needing attention before they publish) come straight off `orders.get_overview`.

**Inventory report's "Stock value over time" is a modelled trend, not a ledger read.** Real per-day
value would need `Stock Ledger Entry.stock_value` (ERPNext's landed-cost valuation) walked per item
per day — expensive and, worse, it prices the shelf in cost terms, whereas the mock (and this
report) prices it in today's selling price, which is what an owner reading "what my shelves are
worth to sell" expects. `get_inventory_report` instead reuses `analytics_dashboard.get_stock_movement`'s
existing day-by-day on-hand walk for the warehouse total and multiplies by today's blended average
selling price. Because this shop's stock was seeded as a single Stock Reconciliation dated at seed
time, the walk-back drifts negative for months before that point — clamped to zero rather than
shown as negative inventory (`ls_shop/api/admin/analytics.py`, `get_inventory_report`).

**Storefront report's "Search terms" table is an honest empty state.** `Storefront Analytics Event`
carries no search-term field at all (`event`, `session_id`, `device`, `item_code`, `path`, `utm_*`
only — checked the doctype). There is nothing to report, so the section stays in the frozen layout
with a stated "not tracked yet" note and an empty list, rather than the old mock's fabricated terms.
Search tracking would need a new event type and a frontend emitter — out of scope here.

**Storefront report's "Top pages" repurposes `analytics_dashboard.get_landing_pages`.** That
function counts landing sessions per page (first page_view of a session), not a raw page-view
count — the doctype has no per-view aggregate endpoint of its own. Labelled "Landing sessions per
page" in the UI rather than silently presenting it as "views" so the number means what it says.

**`catalog.get_recent_product_sales` (used by `ProductDetail.vue`, section 6) still filters
`docstatus == 1`** — the exact draft-COD trap this brief warns about, on a screen outside this
section's scope. Every seeded order is docstatus 0, so a product's "recent sales" panel on its own
detail page currently reads zero units/revenue for the trailing 30 days even for a genuine
bestseller. Not touched here since `ProductDetail.vue` and `catalog.py`'s existing call sites belong
to section 6 and to the agent currently owning `ProductTypes.vue`/import-flow work in this catalog
file; flagging so it isn't re-discovered as a new bug later.

## Add product + bulk import — this commit

**`AddProductDialog.vue` did not exist.** The brief for this session pointed at it as an already-built
prototype to wire, but no such file was in the tree — only the "Add product" dropdown item with a
`toast.info` placeholder. Built new, matching the existing dialog conventions (`VariantDialog.vue`'s
`Dialog` + `FormControl` + section layout, `Attributes.vue`'s `dialog.prompt` for inline "New
collection") rather than inventing a different pattern. It is a single-screen form, not a wizard —
title, collection, one option attribute + its values, sizes (shared across every option, not a
per-option matrix), price/compare-at. Flag if a per-color size matrix or multi-step flow was actually
expected; this is the simplest shape that still drives `catalog.create_product` end to end.

**Abbreviations are not exposed in the Add Product UI.** `create_product` now accepts optional
`option_abbreviations`/`size_abbreviations` overrides (checked by `check_abbreviations_are_distinct`)
so the collision guard is reachable during product creation, not just from the Attributes screen's
`add_attribute_value`. But the dialog never shows a shop owner an "abbreviation" — Shopify doesn't
either, and every other SKU-shaped concept in this app is already read-only for the same reason. The
capability exists for a future bulk-import "variant code" column, and for the verification in this
session's own report; nothing in the frozen UI currently sends it.

**Bulk import's Review step lost its "Download error rows" button.** The original prototype had one;
building a real download-my-failed-rows-as-a-file endpoint was not part of this session's brief
(which asked for per-row errors on screen, not a re-downloadable error file), and a fake button would
have been worse than none. The Run step's finished screen shows the same row/message list instead.
Worth adding if the owner wants to fix-and-re-upload rather than fix-and-retype.

**The Images step (bulk photo matching) is still fully simulated**, per the existing "zip-based bulk
photo import" inert-control note above — its placeholder rows now come from the real uploaded file
instead of a fixed fixture, but drag-a-folder / URL-column / one-by-one matching still fake their
numbers. Out of scope for this session; the real ask (template + working import) does not need it.

**The import template's Collection example is whatever non-group `Item Group` exists first**
(`Apparel` on this seed — the same unfiltered set `catalog.get_collections` already offers, not a
stricter leaf-only list), not a fixed name — `create_product` refuses a collection that does not
already exist,
so a hardcoded example name would 404 on a fresh store with different collections. The importer
itself does not auto-create collections for the same reason: an unapproved "create categories on
import" decision was not made here, matching how `create_product` already behaves for the single-add
dialog.
