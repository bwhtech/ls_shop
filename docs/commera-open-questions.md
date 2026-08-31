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
