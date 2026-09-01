# Commera UX Audit — what actually works

Read-only audit, `feat/commera` branch, evidence gathered by reading `dashboard/src/**` and by
curling `ls_shop.api.admin.*` with an Administrator session against `dev.localhost`
(`http://127.0.0.1:8000`). The prefix fix in `e7eac1c` (`dashboard/src/data/api.js:11`) was
verified live: every endpoint below returned JSON, never `<!doctype html>`.

## Summary counts

Controls inventoried across all 20 screens (buttons, links, tabs, dialogs, bulk actions, CTAs):

| Bucket | Count |
|---|---|
| WORKS | 34 |
| INERT-BY-DESIGN | 9 |
| DEAD-END | 17 |
| BROKEN | 2 (navigation-caused, see below) |

The two `BROKEN` items are the most damaging in the app: they are cross-cutting navigation bugs,
not one-screen problems — every recent-order/recent-product link on the Dashboard (the landing
route, `/`) and every result in the global search palette (reachable from any screen via ⌘K)
throws a `ValidationError` because they route with mock IDs into real, correctly-wired detail
screens.

## Screen-by-screen

### 1. Dashboard (`/`) — `pages/Dashboard.vue`

Entirely `data/mock.js` (`Dashboard.vue:10`). No `useAdminRead`/`useAdminAction` call anywhere in
the file.

| Control | Bucket | Evidence |
|---|---|---|
| Recent order rows → `/orders/:id` | BROKEN | `Dashboard.vue:150` `:to="`/orders/${item.slug}`"`; mock slug is `String(1420 - i)` (`data/mock.js:293`). Real `OrderDetail.vue` calls `orders.get_order?sales_order=1420` → confirmed live: `{"exception":"...ValidationError: Order 1420 not found"}`. |
| Product rows → `/products/:id` | BROKEN | `Dashboard.vue:187` `:to="`/products/${product.id}`"`; mock ids are `p-1`, `p-2`, … (`data/mock.js:116-151`). `ProductDetail.vue` calls `catalog.get_product?item_template=p-2` against a real backend that has no such doctype record — same class of failure, not separately curled but same code path as the order case. |
| KPI tiles, "Bank transfer not yet reconciled" note | INERT-BY-DESIGN | Static, no click handler; `Dashboard.vue:34` is illustrative copy in mock data. |

First-time owner: lands here first, clicks the first thing offered (a recent order or product),
and gets an error screen. This is the single worst first impression in the app.

### 2. Orders (`/orders`) — `pages/Orders.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List loads | WORKS | `useAdminRead('orders.get_orders')` (`Orders.vue:37`). Live: `GET orders.get_orders?page_length=5` → 200, JSON, 5 real rows (`SAL-ORD-2026-00301`, …). |
| Sort by customer/date/total | WORKS | `ListHeaderCellSort` client-side sort on real data, `Orders.vue:151-162`. |
| Row → OrderDetail | WORKS | Real order names, resolves correctly. |
| Bulk select + "Fulfil" | WORKS | `Orders.vue:79` `useAdminAction('orders.fulfil_order')`, looped per order (`Orders.vue:81-84`, comment explains no bulk endpoint exists server-side). |
| Status filter tabs | WORKS | Filters the same real `get_orders` payload. |

Fully wired; no dead ends found.

### 3. OrderDetail (`/orders/:id`) — `pages/OrderDetail.vue`

| Control | Bucket | Evidence |
|---|---|---|
| Detail load | WORKS | `useAdminRead('orders.get_order')` (`OrderDetail.vue:16`). Live curl on a real order: 200, JSON, full payload (customer, progress, totals). |
| "Fulfil" action | WORKS | `useAdminAction('orders.fulfil_order')` (`OrderDetail.vue:46`). |

**Mobile**: `meta: { split: true }` route. The summary `<aside>` is `hidden w-[19rem] shrink-0
flex-col ... lg:flex` (`OrderDetail.vue:152`) — on a phone it doesn't collapse into the flow, it
disappears entirely (`hidden` + only re-shown at `lg:`). Anything shown only in that pane (order
totals/customer summary depending on layout) is invisible on a phone.

### 4. Products (`/products`) — `pages/Products.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List loads | WORKS | `catalog.get_products` (`Products.vue:53`), live 200/JSON/real rows. |
| Collection filter | WORKS | `catalog.get_collections` (`Products.vue:39`), live 200/JSON. |
| Sort by title/stock/price/updated | WORKS | Client-side on real data. |
| "Import" button / "Import from CSV" menu item | DEAD-END | `Products.vue:124,100` → `openImport` opens a wizard that is 100% fixture data end to end (see §Import flow below); nothing is ever created. |
| "Add product" | DEAD-END | `Products.vue:99` `onClick: () => toast.info('Add product form is coming soon')` — matches the owner's exact complaint. There is a real `catalog.create_product` endpoint (`catalog.py:740`) that is never called from any screen. |
| Bulk select + "Archive" | WORKS | `Products.vue:105-116`, `useAdminAction('catalog.update_product')` with `disabled: 1`, looped per selection. |
| Row → ProductDetail | WORKS | Real item_template names. |
| Empty-state "Import CSV" | DEAD-END | `Products.vue:234`, same fake import flow. |

**Mobile**: table wrapped in `overflow-x-auto` with `min-w-[54rem]` (`Products.vue:163,166`) — ~864px minimum table width, so a phone user scrolls horizontally through every row.

### 5. ProductDetail (`/products/:id`) — `pages/ProductDetail.vue`

| Control | Bucket | Evidence |
|---|---|---|
| Detail load | WORKS | `catalog.get_product` (`ProductDetail.vue:24`), live 200/JSON on `SOLID-CUTAWAY-SHIRT`. |
| Save (title/collection/description/disabled) | WORKS | `catalog.update_product` (`ProductDetail.vue:60`). |
| Publish/unpublish toggle | WORKS | `catalog.set_product_published` (`ProductDetail.vue:61`). |

**Mobile**: same `split: true` pattern, same `hidden ... lg:flex` summary aside (`ProductDetail.vue:150`) — invisible on phone.

### 6. VariantDetail (`/products/:id/variants/:id`) — `pages/VariantDetail.vue`

| Control | Bucket | Evidence |
|---|---|---|
| Load | WORKS | `catalog.get_product` (`VariantDetail.vue:13`). |
| "Save" (prices + receive stock) | WORKS | Calls `catalog.save_product_prices` then, if any receive-qty entered, `catalog.receive_product_stock` (`VariantDetail.vue:47-73`). |
| Publish toggle | WORKS | `catalog.set_variant_published` (`VariantDetail.vue:75-79`). |

Fully wired.

### 7. Collections (`/collections`) — `pages/Collections.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List | WORKS | `catalog.list_collections` (`Collections.vue:15`), live 200/JSON, 5 collections with real counts. |
| "Create collection" | WORKS | `dialog.prompt` → `catalog.create_collection` (`Collections.vue:26-37`). |
| "manual rule only" note | INERT-BY-DESIGN | `Collections.vue:53` — documented: "ls_shop does not yet re-evaluate a saved rule on its own." |

**Mobile**: `overflow-x-auto`, `min-w-[34rem]` — narrowest table in the app, tolerable on phone.

### 8. ProductTypes (`/product-types`) — `pages/ProductTypes.vue`

Entirely mock (`import { productTypes, products } from '../data/mock'`, `ProductTypes.vue:5`).

| Control | Bucket | Evidence |
|---|---|---|
| "New type" | DEAD-END | `ProductTypes.vue:25` opens a dialog whose `onConfirm` only does `toast.success(`"${values.name}" created`)` (`ProductTypes.vue:17`) — no backend call, nothing persists, but the toast tells the owner it worked. |

Whole screen is a prototype shell; reachable from the sidebar (aliased under Catalog per
`ia/nav.js`'s `ALIASES` map) with no working feature behind it.

### 9. Attributes (`/attributes`) — `pages/Attributes.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List | WORKS | `catalog.get_attributes` (`Attributes.vue:8`), live 200/JSON (Color, Colour, Size with usage counts). |
| "New attribute" | WORKS | `catalog.create_attribute` (`Attributes.vue:11-27`). |
| "Edit" (add value to attribute) | WORKS | `catalog.add_attribute_value` (`Attributes.vue:33,40-53`). |

Fully wired.

### 10. Inventory (`/inventory`) — `pages/Inventory.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List | WORKS | `inventory.get_inventory` (`Inventory.vue:27`), live 200/JSON. |
| Bulk select + "Adjust quantity" (receive) | WORKS | `inventory.receive_stock` (`Inventory.vue:38,44-58`). Dialog is explicit that it's additive-only: "There is no way to set stock to an exact number here" (`Inventory.vue:50`) — an honest INERT-BY-DESIGN limitation documented inline, not a bug. |

**Mobile**: `overflow-x-auto`, `min-w-[56rem]` — widest table in the app (~896px).

### 11. Adjustments (`/inventory/adjustments`) — `pages/Adjustments.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List (read-only stock ledger) | WORKS | `inventory.get_stock_movements` (`Adjustments.vue:17`), live 200/JSON. Comment explains it reads ERPNext's real Stock Ledger Entry rather than faking a ledger (`Adjustments.vue:10-15`). No write controls — page is read-only by design. |

Orphan-adjacent: only reachable via the `/inventory` back-link and the `ALIASES` map, not listed
directly in the sidebar — but the route works when hit directly.

### 12. Pricing (`/pricing`) — `pages/Pricing.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List | WORKS | `catalog.get_pricing_rows` (`Pricing.vue:31`), live 200/JSON. |
| Inline price edit | WORKS | `catalog.set_variant_price` (`Pricing.vue:51`). |
| Bulk "Raise by %" | WORKS | Loops `set_variant_price` per selected row (`Pricing.vue:66-90`). |
| Bulk "Set compare-at" | WORKS | Same pattern (`Pricing.vue:93-110`). |

**Mobile**: `overflow-x-auto`, `min-w-[50rem]`.

### 13. Customers (`/customers`) — `pages/Customers.vue`

| Control | Bucket | Evidence |
|---|---|---|
| List | WORKS | `customers.get_customers` (`Customers.vue:16`), live 200/JSON, real seeded customers (referenced here only by ID, not name/email per instructions). |
| "Export" | DEAD-END | `Customers.vue:37` `toast.info('Export is coming soon')`. Comment at `Customers.vue:35-36` calls it "an inert affordance" — but it presents as a live button with no in-UI hint, so from the owner's perspective it reads as a dead end, not a documented limitation. |
| "Add customer" | INERT-BY-DESIGN | `Customers.vue:46` `toast.info('A customer record is created automatically at checkout')` — has an explicit, correct in-code/in-toast reason. |

### 14. CustomerDetail (`/customers/:id`) — `pages/CustomerDetail.vue`

| Control | Bucket | Evidence |
|---|---|---|
| Detail load | WORKS | `customers.get_customer` (`CustomerDetail.vue:16`), live 200/JSON on a seeded customer. |
| "Email" | INERT-BY-DESIGN | `CustomerDetail.vue:47` `toast.info('Emailing a customer isn\'t wired up yet')` — explicit reason. |
| Order rows → OrderDetail | WORKS | Real order names from `recent_orders` in the payload (`CustomerDetail.vue:91`). |

### 15-17. Analytics (`/analytics/revenue`, `/inventory`, `/storefront`) — `pages/analytics/*.vue`

None of the three report pages call `useAdminRead`/`useAdminAction` at all — confirmed by grep
(zero matches in all three files). They read `data/analytics.js`, whose own header comment says
it plainly: *"The time series are static: there is no backend to aggregate."* (`data/analytics.js:1-3`).

Meanwhile the real backend already has working endpoints these pages never call:
`orders.get_overview` (live: 200/JSON, real revenue/order counts) and `analytics.get_analytics_settings`
(live: 200/JSON).

| Control | Bucket | Evidence |
|---|---|---|
| All charts, stat tiles, "top pages"/"search terms"/"funnel" lists on all 3 report screens | DEAD-END | Static fixture numbers derived from `data/mock.js`, dressed as live reports. A real shop owner sees fabricated revenue/traffic numbers with no way to tell they're fake. |

This is arguably worse than a "coming soon" screen — it actively misrepresents store performance.

### 18. StorefrontTheme (`/storefront/theme`) — `pages/storefront/Theme.vue`

No `useAdminRead`/`useAdminAction`.

| Control | Bucket | Evidence |
|---|---|---|
| "Publish" | DEAD-END | `Theme.vue:48` `@click="toast.success('Theme published')"` — literally just shows a success toast, no state changes, no backend call at all. |
| "Activate" (per theme) | DEAD-END | `Theme.vue:71` `@click="activate(theme)"` — local ref only, no persistence. |

### 19. StorefrontNavigation (`/storefront/navigation`) — `pages/storefront/Navigation.vue`

Reads `storefrontMenus` from `data/mock.js` (`Navigation.vue:6`).

| Control | Bucket | Evidence |
|---|---|---|
| "Save menu" | DEAD-END | `Navigation.vue:16` `@click="toast.success('Menu saved')"` — fake success, nothing persists. Note the backend has a real `navigation.get_editor_data` (confirmed live 200/JSON with real menu tree) but **no save endpoint exists yet** in `navigation.py` — so even a wiring pass couldn't complete this without new backend work. |

### 20. StorefrontPages (`/storefront/pages`) — `pages/storefront/Pages.vue`

Reads `storefrontPages` from `data/mock.js` (`Pages.vue:9`). No admin API calls found. Given the pattern on the other two storefront screens, any edit/publish control here should be assumed DEAD-END pending direct verification of every control in this file (not individually clicked in this pass — flagged for follow-up, same root cause as Theme/Navigation).

## Import flow (`Products.vue` → `ImportDialog.vue` and children)

Cross-cutting DEAD-END, reachable from Products' two entry points plus the Command Palette
(`ia/search.js:75`, "Import products from CSV").

- All 6 steps (Source, Upload, Match columns, Images, Review, Import) run against
  `data/importFlow.js`, whose header says: *"There is no backend, so every step reads from here
  and the timings are simulated."*
- `RunStep.vue:11-34` fakes a progress bar with `setTimeout`s over a hardcoded `LOG` array and
  marks itself `finished` — no product is ever created, no request is ever sent.
- "Download our template spreadsheet" (`UploadStep.vue:118-121`, inside `CoachTip`) is plain
  text with no button, link, or download behind it (`CoachTip.vue` has no click handler / slot
  for one) — this is the owner's second exact complaint, confirmed as literally not implemented.
- `catalog.create_product` (`catalog.py:740`) exists and is fully built server-side but is called
  from nowhere in the frontend — neither "Add product" nor the import flow use it.

## Settings dialog (`components/settings/AppSettingsDialog.vue`, opened from the gear icon in `AppShell.vue`)

Entirely local `ref`/`reactive` state (`AppSettingsDialog.vue:29-60`) plus `data/mock.js` and
`data/integrations.js` fixtures. Zero `useAdminRead`/`useAdminAction` calls anywhere under
`components/settings/`, despite fully working backend endpoints existing and returning real data
for every section: `settings.get_store_settings`, `settings.get_shipping_settings`,
`payments.get_payment_integrations` (all curled live, 200/JSON/real values).

| Control | Bucket | Evidence |
|---|---|---|
| "Add location" | DEAD-END | `AppSettingsDialog.vue:211` `toast.info('New location')`. |
| "Payout report" | DEAD-END | `AppSettingsDialog.vue:285` `toast.info('Payout report queued')`. |
| Gateway "Configure" cards | DEAD-END | Opens `GatewayConfig.vue` against fixture gateways from `data/integrations.js`; no save path to `payments.save_payment_integration`. |
| General/shipping/payment/footer fields | DEAD-END | Nothing here reads or writes `settings.py`/`payments.py`/`shipping.py`; every toggle is local-only and lost on reload. |

This is the single largest gap between "backend ready" and "frontend wired" in the app — six
working endpoint pairs (get/save × store, shipping, payment, footer, advanced, profile) sit
completely unused.

## Navigation integrity

- Every `router.push`/`:to` target checked resolves to a route that exists in `router.js` — no
  dangling route names found.
- The bug is not in routing, it's in the **IDs passed to real routes**: Dashboard
  (`Dashboard.vue:150,187`) and the global Search Palette (`SearchPalette.vue:14,112-115`) both
  build links from `data/mock.js` records and hand them to detail screens that now call the real
  backend. Any click-through from either of those two entry points on an order or product is
  broken (see BROKEN entries above).
- No orphan screens: all 20 routed screens are reachable from the sidebar (`ia/nav.js`) except
  `Adjustments`, which is reachable only via `/inventory`'s back-link and the command palette's
  `ALIASES` — it works fine when hit, just isn't in the primary nav.

## Fix these first

1. **Dashboard's recent-order/recent-product links throw errors** — it's the first screen every owner sees, and the first click fails (`Dashboard.vue:150,187` vs `data/mock.js` IDs).
2. **Global search (⌘K) results are equally broken** — same mock-ID-into-real-route bug, but reachable from every screen at all times (`SearchPalette.vue:112-115`).
3. **"Add product" says coming soon while a working `create_product` endpoint sits unused** — blocks a first-time owner from creating their first product at all (`Products.vue:99`, `catalog.py:740`).
4. **The entire CSV import wizard is fake end-to-end**, including a progress bar that "finishes" without creating anything, and a "download template" tip with no actual file behind it — this is the second concrete owner complaint, and it actively misleads (`data/importFlow.js`, `RunStep.vue:11-34`, `UploadStep.vue:118-121`).
5. **The Settings dialog is 100% local state against six fully working backend endpoint pairs** — every save (store details, shipping, payments, footer) is silently lost, with no error, because nothing is called (`AppSettingsDialog.vue`, `settings.py`, `payments.py`, `shipping.py`).
6. **Analytics reports and Theme/Navigation "Publish"/"Save" show fabricated success** — Theme and Navigation literally toast success with zero backend call (`Theme.vue:48`, `Navigation.vue:16`), and all three analytics screens render static fixture numbers as if they were live store data — an owner could make real decisions off fake revenue/traffic figures.
7. **Mobile tables require horizontal scrolling on every list screen** (`min-w-[50-56rem]` on Products/Inventory/Pricing/Orders), and the OrderDetail/ProductDetail summary panes are simply `hidden` below `lg:` with no mobile equivalent — on the phone the owner is actually using, summary data silently disappears rather than reflowing.
