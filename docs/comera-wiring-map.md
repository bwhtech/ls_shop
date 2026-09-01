# Comera Wiring Map

Branch `feat/comera`. `dashboard/` is Comera, a Vue 3 + frappe-ui SPA prototype. Every screen currently
reads fake data from `dashboard/src/data/mock.js` (plus `dashboard/src/data/analytics.js` for the
Analytics section) and every write action just raises a toast. This document is the brief for wiring
each section to the real `ls_shop` backend, one at a time. Read it before re-deriving any of this.

Domain facts assumed throughout:
- ls_shop is standalone — it does **not** depend on the `webshop` app. Products live in
  `Style Attribute Configurator` / `Style Attribute Variant`, not `Website Item`. Any `Website Item`
  reference anywhere in the codebase is legacy and should be ignored.
- `ls_shop/api/return.py` is named after a Python keyword and can only be imported via `importlib`.
- Store-wide config lives in the `Lifestyle Settings` single doctype.

---

## 1. Screen inventory

21 entries in `dashboard/src/router.js`: 20 map to a page component, `/analytics` is a bare redirect to
`/analytics/revenue` with no component of its own.

| Route | Component | Description | Write actions (toast-only) | mock.js exports used |
|---|---|---|---|---|
| `/` | `pages/Dashboard.vue` | KPI strip, "needs attention" list, revenue chart, recent orders, top products | none — buttons are `route` links | `inventory, kpis, orders, products` (+ `revenueByMonth` from `data/analytics.js`, not `mock.js`) |
| `/orders` | `pages/Orders.vue` | Order list: tabs (all/unfulfilled/unpaid/open/closed), search, sort, bulk select | `markFulfilled()` → toast "N order(s) marked fulfilled"; "Export", "Create order", "Print packing slips" have no handler at all | `orders` |
| `/orders/:id` | `pages/OrderDetail.vue` | Single order: progress, line items, totals; sidebar customer/address/tags/note | `fulfil()` mutates `order.fulfillment='fulfilled'` + toast; `refund()` via confirm dialog mutates `order.payment='refunded'` + toast; dropdown: Duplicate (toast.info), Print invoice (toast.info), Cancel order (confirm → toast) | `customers, orders` (+ `erpnextLink` from `data/erpnext.js`) |
| `/products` | `pages/Products.vue` | Product list: status/type tabs, search, sort, bulk select | "Add product" dropdown → toast.info; "Import from CSV" opens the (unwired) import flow; bulk "Add to collection"/"Archive" have no handler | `productTypes, products` |
| `/products/:id` | `pages/ProductDetail.vue` (+ 7 sub-components under `components/product/` + `VariantEditor.vue`) | Product edit form: basics, type fields, pricing, variants, stock, storefront, organization; right-rail summary | top-level `save()` → toast "Saved"; VariantEditor "Add option" → toast; bulk-edit-variant dialog → toast | top-level `products`; `ProductTypeFields` → `productTypes`; `ProductStock` → `inventory`; `ProductOrganization` → `collections, productTypes`; `VariantEditor` → `attributes, regenerateVariants` |
| `/products/:id/variants/:variantId` | `pages/VariantDetail.vue` | Single variant: photos, option values, price/compare-at/SKU/barcode, per-location stock | "Save" button → inline `toast.success('Variant saved')`, no real handler | `inventory, products` |
| `/collections` | `pages/Collections.vue` | Collections list (manual/smart), paginated | "Create collection" has no handler | `collections` |
| `/product-types` | `pages/ProductTypes.vue` | Product-type list with field schema, counts | `addType()` → prompt dialog (name, fields) → toast, not persisted; row "Edit" has no handler | `productTypes, products` |
| `/attributes` | `pages/Attributes.vue` | Attribute list with values, usage counts | `addAttribute()` → prompt dialog → toast; row "Edit" has no handler | `attributes` |
| `/inventory` | `pages/Inventory.vue` | Stock list: low-stock filter, search, bulk select, editable on-hand input (unwired) | `adjust()` → toast "Adjustment recorded for N lines"; "Receive stock", "Transfer" have no handler | `inventory` |
| `/inventory/adjustments` | `pages/Adjustments.vue` | Read-only stock-movement ledger | none — explicitly read-only | `adjustments` |
| `/pricing` | `pages/Pricing.vue` | Flattened price-edit table (one row per sellable unit), editable price inputs (unwired), bulk select | `bulkPrice()` → toast "Price rule queued for N items" (used for both "Raise by %" and "Set compare-at"); "Price rules", "Export prices" have no handler | `productTypes, products` (reshaped client-side — see §2) |
| `/customers` | `pages/Customers.vue` | Customer list with search | "Export", "Add customer" have no handler | `customers` |
| `/customers/:id` | `pages/CustomerDetail.vue` | Customer profile: stats (orders/spend/AOV), recent orders | "Email customer" has no handler | `customers, orders` |
| `/analytics` | — (redirect) | redirects to `/analytics/revenue` | — | — |
| `/analytics/revenue` | `pages/analytics/Revenue.vue` | Revenue report: stat cards, area/bar charts, by-month table | none, read-only | none — uses `revenueByMonth` from `data/analytics.js` |
| `/analytics/inventory` | `pages/analytics/Inventory.vue` | Inventory report: stat cards, stock-value chart, sell-through/cover charts, dead-stock table | none | none — uses `coverByProduct, deadStock, sellThrough, stockValue, stockValueByMonth, unitsOnHand` from `data/analytics.js` |
| `/analytics/storefront` | `pages/analytics/Storefront.vue` | Storefront report: sessions, channel donut, funnel, top pages, search terms | none | none — uses `channels, funnel, searchTerms, sessionsByMonth, topPages` from `data/analytics.js` |
| `/storefront/theme` | `pages/storefront/Theme.vue` | Theme picker + brand/shape/product-page toggles + live token preview | `activate(theme)` mutates a local `themes` array + toast; "Publish" → toast; all Select/Slider/Switch bindings are local refs, never persisted | none — data is hardcoded locally (`themes`, `ACCENTS`, etc.), not from `mock.js` |
| `/storefront/navigation` | `pages/storefront/Navigation.vue` | Menu editor: tab per menu, nested item list, mini preview | "Add item", per-item "Edit"/"Remove" have no handler; "Save menu" → toast | `storefrontMenus` |
| `/storefront/pages` | `pages/storefront/Pages.vue` | CMS page list: title/path/status/sections/updated, paginated | "Add page" has no handler | `storefrontPages` |

Important: **`data/analytics.js` is a separate module from `mock.js`.** It re-derives its series from
`mock.js`'s `orders`/`products` client-side (see §2 note on `Revenue`/`Inventory`/`Storefront` analytics),
but none of the three Analytics pages import `mock.js` directly.

---

## 2. Mock data contract

`dashboard/src/data/mock.js`, 401 lines, 14 named exports in file order. Field types are inferred from
real sample records — this is the contract the real endpoints must satisfy field-for-field.

### `locations` — array
`{ id: 'loc-1', name: 'Bengaluru warehouse', code: 'BLR' }` — `id`/`name`/`code` strings. Only one record
exists (single-warehouse prototype).

### `productTypes` — array (schema definitions, not data)
```js
{ id: 'book', name: 'Book', icon: 'lucide-book-open',
  fields: [{ key: 'author', label: 'Author', type: 'text' },
           { key: 'language', label: 'Language', type: 'select', options: ['English','Hindi','Kannada'] }] }
```
`id`/`name`/`icon` strings; `fields[]` of `{ key, label, type: 'text'|'number'|'select'|'textarea', options?: string[] }`.
Defines the dynamic per-type fields a product carries.

### `attributes` — array
`{ id: 'size', name: 'Size', values: ['XS','S','M','L','XL'], usedBy: 6 }` — `values` is `string[]`;
**`usedBy` is DERIVED** (products-using-this-attribute count) and is hardcoded, not computed from `products`.

### `collections` — array
`{ id: 'col-1', title: 'New arrivals', rule: 'smart', count: 12, condition: 'Created in last 30 days' }`
— `rule` enum `smart|manual`; `condition` is a human-readable rule string (`'—'` sentinel for manual).
**`count` is DERIVED** — hardcoded, not an actual count of matching products.

### `products` — reactive array (the core catalog entity)
Base record:
```js
{ id: 'p-1', title: 'The Midnight Library', type: 'book', status: 'active', thumb: '📗',
  vendor: 'Canongate', sku: 'BK-MIDLIB', price: 499, compareAt: 699,
  tags: ['fiction','bestseller'], collections: ['col-1','col-2'], updated: '2026-08-28',
  typeFields: { author: 'Matt Haig', isbn: '9781786892737', publisher: 'Canongate', pages: 288, language: 'English' },
  options: [{ name: 'Format', values: ['Paperback','Hardcover','Ebook'] }],
  description: 'Between life and death there is a library...' }
```
`type` is FK → `productTypes.id`; `status` enum `active|draft|archived`; `compareAt` number|null; `collections`
is FK array → `collections.id`; `typeFields` shape varies per `productTypes[type].fields[].key`; `options[]`
are variant axes (`{ name, values: string[] }`).
**After `reactive()` wrap, 3 fields are computed at load time**, not present in the raw seed: `variants`
(array, below), `stock` (sum of variant stock or pseudo-random fallback), `hasVariants` (`variants.length > 0`).

`variants[]` sub-shape:
```js
{ id: 'p-1-v1', productId: 'p-1', title: 'Paperback', combo: [{ name: 'Format', value: 'Paperback' }],
  sku: 'BK-MIDLIB-PAP', price: 499, compareAt: 699, stock: 23, committed: 2,
  thumb: '📗', images: 2, barcode: '899000137' }
```
`price` is **DERIVED**: base price + hardcoded per-option surcharge (e.g. +400 Hardcover, +100 XL);
`stock`/`committed` are deterministic pseudo-random; `images` (count) and `barcode` are synthesized, not real.

### `regenerateVariants(product)` — function, not data
Mutates `product.variants` / `hasVariants` / `stock` in place by rebuilding the variant matrix from
`options`. Any "save product" endpoint that changes `options` needs an equivalent server-side rebuild.

### `customers` — array
`{ id: 'c-1', name: 'Aarti Mehta', email: 'aarti@example.com', city: 'Bengaluru', orders: 7, spend: 24800, since: '2025-02-11' }`
— **`orders` and `spend` are DERIVED** lifetime aggregates, hardcoded rather than computed from the `orders` export.

### `orders` — array (built by seeded `buildOrders()`)
```js
{ id: '#1420', slug: '1420', customerId: 'c-3', customer: 'Farida Sheikh', email: 'farida@example.com',
  date: '2026-08-31', time: '09:00', payment: 'paid', fulfillment: 'fulfilled',
  channel: 'Online store', location: 'Bengaluru warehouse',
  items: [{ productId: 'p-6', title: 'Atomic Habits', variantTitle: 'Hardcover', sku: 'BK-ATHAB-HAR',
            thumb: '📙', qty: 1, price: 999 }],
  subtotal: 999, shipping: 0, tax: 50, total: 1049,
  address: { line1: '4th Cross, Indiranagar', city: 'Mumbai', pin: '560038', country: 'India' },
  tags: ['priority'], note: 'Customer asked for gift wrap.' }
```
`id` is `#`-prefixed display id, `slug` is the route id; `payment` enum `paid|pending|refunded|partially_refunded`;
`fulfillment` enum `unfulfilled|fulfilled|partial|delivered|cancelled`; `channel` enum `POS|Online store`;
`customer`/`email`/`location` are denormalized. **`subtotal`/`tax`/`total` are computed** (`shipping` = free
above ₹3000 else ₹79 flat; `tax` = 5% of subtotal). `address.pin` is a mock artifact — hardcoded `'560038'`
for every order regardless of city.

### `inventory` — array (flattened product × variant × location)
`{ id: 'p-1-v1-loc-1', productId: 'p-1', productTitle: 'The Midnight Library', variantId: 'p-1-v1', variantTitle: 'Paperback', sku: 'BK-MIDLIB-PAP', thumb: '📗', locationId: 'loc-1', location: 'Bengaluru warehouse', onHand: 23, committed: 2 }`
— one row per (variant, location) pair; `productTitle`/`location` denormalized.

### `adjustments` — array
`{ id: 'adj-1', date: '2026-08-30', sku: 'AP-LINSH-M-SAN', product: 'Everyday Linen Shirt', delta: +24, reason: 'Received', by: 'Aarti' }`
— `delta` signed number; `reason` free-text-ish (`Received|Damaged|Stock count` seen); `by` is a display
name, not a User id/email (no FK).

### `storefrontMenus` — array (nested tree, 2 levels)
```js
{ id: 'main', name: 'Main navigation',
  items: [{ id: 'm1', label: 'Shop', target: '/collections/all',
            children: [{ id: 'm1a', label: 'New arrivals', target: '/collections/new-arrivals' }] }] }
```
`children` recurses the same shape but the mock never populates a 3rd level.

### `storefrontPages` — array
`{ id: 'sp-1', title: 'Home', slug: '/', status: 'published', sections: ['Hero','Featured collection','Editorial','Newsletter'], updated: '2026-08-30' }`
— `sections` is just a list of block-type labels, no per-section content/config in the mock.

### `kpis` — array (Dashboard tiles)
`{ key: 'revenue', label: 'Revenue', value: '₹4,82,300', delta: '+12.4%', trend: 'up' }` — **`value` and
`delta` are entirely pre-formatted strings** (currency + Indian digit grouping, or percent; note `delta`
mixes `%` and `pt` suffixes across tiles), `trend` enum `up|down`.

### `salesSeries` — plain array of numbers
`[22, 31, 28, 44, ... ]` (31 integers, presumably last-31-days). No accompanying date labels — a real
endpoint must decide those.

### Cross-cutting notes
- No dead exports — every export is referenced somewhere (22 files import from `mock.js`).
- **`pages/Pricing.vue` has no dedicated mock export.** It imports `productTypes` + `products` and
  reshapes via `computed()`: flatMaps each product to one row per variant, picking
  `{ id, title, subtitle: variantTitle, sku, thumb, price, compareAt }`, then computes margin client-side
  as `((price - price*0.55) / price) * 100` — a **hardcoded 55% assumed-COGS constant**. There is no real
  cost/margin field anywhere in the mock, confirming Pricing has no backing data model as-is.
- `dashboard/src/data/analytics.js` (114 lines) is a **separate file from `mock.js`**, imported only by the
  three Analytics pages. It derives `revenueByMonth`, `stockValue`, `unitsOnHand`, `stockValueByMonth`,
  `sellThrough`, `coverByProduct`, `deadStock` from `mock.js`'s `orders`/`products` with baked-in monthly
  weight curves and constants (e.g. `REVENUE`/`ORDER_COUNT` arrays for 12 named months, `SESSIONS` array).
  `sessionsByMonth`, `channels`, `funnel`, `topPages`, `searchTerms` are pure hardcoded arrays with **no
  connection to any other mock data** — they represent real web-analytics data (GA4/pixel), not store data.

---

## 3. Existing backend surface

All functions under `ls_shop.api.admin.*`. 37 directly `@frappe.whitelist()`-decorated across the 10 files,
plus 22 re-exported-by-reference whitelisted functions (footer.py re-exports 10 from `footer_preview`,
navigation.py re-exports 12 from `navbar_manager`) — **59 total reachable paths**.

### analytics.py (2)
- `get_analytics_settings()` — GET, System Manager only. Returns `Analytics Settings` single: plain fields
  (`enable_first_party, enable_ga4, ga4_measurement_id, ga4_property_id, enable_facebook, fb_pixel_id`) +
  `ga4_service_account_json_is_set, fb_access_token_is_set` (bool) + `ga4_configured, meta_configured` (bool)
  + `custom_tracking_scripts: [{title, enabled, script}]`.
- `save_analytics_settings(**kwargs)` — POST. Writes tracking config; returns same shape as above.
- **This file is tracking-pixel *configuration* only — it has no report/aggregation data.** No endpoint here
  can serve `Revenue`/`Inventory`/`Storefront` analytics screens.

### catalog.py (10)
- `get_products(search=None, start=0, page_length=20)` — Returns `{products: [...], total, currency}`.
  Each product: `{name, title, image, collection, disabled, variant_count, published_count, price_from,
  price_to, stock, variants: [{name, option, is_published, route, size_count}]}`. Reads
  `Style Attribute Configurator, Item, Style Attribute Variant, Color Size Item, Item Price, Bin,
  Website Slideshow Item`.
- `get_product(item_template)` — Returns `{name, title, image, collection, description, disabled,
  option_attribute, variants: [{name, option, is_published, route, storefront_url, sizes: [{size,
  item_code, rate, stock}], images: [url...], blockers: [str...]}]}`.
- `get_collections(search_text=None)` — Returns `list[str]` (Item Group names, limit 100). **Item Group has
  no smart/manual rule concept** — this is a flat name list, not the mock `collections` shape.
- `get_attribute_values(attribute)` — Returns `list[str]` (`Item Attribute Value` values for one attribute).
- `create_product(title, collection, option_attribute, size_attribute, option_sizes, price=None, sale_price=None)`
  — POST. Creates `Item` template+variants, `Style Attribute Configurator` (→ generates
  `Style Attribute Variant` rows), optionally sets `Item Price`. Returns `{name}`.
- `update_product(item_template, title=None, collection=None, description=None, disabled=None)` — POST.
  Returns `{name}`.
- `set_variant_published(style_attribute_variant, publish)` — POST. Returns `{name, is_published}`.
- `add_product_images(style_attribute_variant, file_urls)` — POST. Returns `{name, images: [url...], blockers}`.
- `remove_product_image(style_attribute_variant, file_url)` — POST. Returns `{name, images, blockers}`.
- `save_product_prices(style_attribute_variant, size_prices)` — POST. Writes `Item Price` rows; return
  shape defined in the `Style Attribute Variant` controller, not this file.
- `receive_product_stock(style_attribute_variant, received_quantities, valuation_rates=None)` — POST.
  Submits a Material Receipt Stock Entry; returns `{stock_entry: <controller-defined>}`.
- `set_product_published(item_template, publish)` — POST. Bulk-toggles all options' `is_published`.
  Returns `{updated: [label...], skipped: [label...]}`.
- Note: `get_unpublishable_options()` in this file is an **internal helper**, not whitelisted — consumed by
  `orders.get_overview` for the "needs attention" panel.

### footer.py (2 own + 10 re-exported)
Re-exported from `footer_preview`: `get_editor_data` (GET, returns `{columns: [{name, title,
section_order, enabled, links: [{name, parent, link_label, link_url, link_order, enabled}]}], pages:
[{name, route}], modified}`), `add_section`, `rename_section`, `delete_section`, `reorder_sections`,
`add_link`, `update_link`, `delete_link`, `reorder_links`, `move_link` — all POST, all return the same
editor-data shape as `get_editor_data`.
Own: `set_section_enabled(name, enabled)`, `set_link_enabled(section_name, link_row_name, enabled)` — both
POST, both write `Lifestyle Settings.footer_sections` / its child `Footer Section Config.footer_links`,
both return editor data.

### integrations.py (0)
No whitelisted functions — shared provider-agnostic engine (`describe_integration`, `save_integration`,
`write_settings`, `save_profile`) consumed by `payments.py` and `shipping.py`.

### inventory.py (2)
- `get_inventory(availability=None, search=None, start=0, page_length=50)` — Returns `{rows: [{item_code,
  product, product_name, option, variant, size, stock, is_published, availability}], total, low_stock_threshold: 5}`.
  Reads `Style Attribute Variant, Color Size Item, Item, Bin`.
- `receive_stock(received_quantities)` — POST. Submits Stock Entries across mixed products/variants.
  Returns `{stock_entries: [...]}`. **This is receiving only — no generic "adjustment with reason" op.**

### navigation.py (2 own + 12 re-exported)
Re-exported from `navbar_manager`: `add_node`, `update_node`, `delete_node`, `delete_all_nodes`,
`get_delete_preview`, `get_delete_all_preview`, `move_node`, `import_from_item_group`, `set_visibility`,
`get_cascade_products`, `get_publish_preview`, `set_published` — all operate on `Ecommerce Category`, all
return `{menu: [...tree...]}` (except the preview/count ones). Note: `navbar_manager.reorder_nodes` is
whitelisted but **not re-exported** here — currently unreachable at `admin.navigation.*`.
Own: `get_editor_data()` — Returns `{menu: [...tree...], max_depth}` (tree from `navbar_manager.get_menu_tree()`,
per-node keys not defined in this file). `get_link_options(doctype, search_text=None)` — Returns
`list[{label, value}]` for `Item Group`/`Brand`.

### orders.py (4)
- `get_orders(status=None, search=None, start=0, page_length=20)` — Returns `{orders: [{name, customer,
  placed_on, status, state: {key, label}, total, currency, item_count, payment_mode}], total}`.
- `get_order(sales_order)` — Returns `{name, customer, email, phone, placed_on, status, state: {key,label},
  progress: [{key, label, state, at, note}], currency, total, net_total, shipping, cod_charge, tax,
  total_taxes_and_charges, grand_total, payment_mode, shipping_address, can_fulfil, items: [{item_code,
  title, size, qty, delivered_qty, rate, amount, image}], deliveries: [name...]}`.
- `fulfil_order(sales_order)` — POST. Creates+submits a `Delivery Note`. Returns `{delivery_note: name}`.
  **Single-order only — no bulk-fulfil.**
- `get_overview(order_status=None)` — Returns `{currency, window_days: 30, stats: [{key, label, value,
  format, delta, note?}] (4: revenue/orders/to_fulfil/products_live), recent_orders: [...up to 5, get_orders
  shape...], running_low: [...up to 5, get_inventory shape...], needs_attention: [{variant, product, title,
  option, blockers}] (up to 5)}`. Backs `Dashboard` closely, no `refund`/`cancel` endpoint anywhere in this file.

### payments.py (2)
- `get_payment_integrations()` — System Manager only. Returns `list[card]` for `razorpay, stripe, telr,
  tabby`, each `{slug, label, blurb, settings_doctype, available, enabled, configured, missing:
  [fieldname...], webhook_url, docs_url, groups: [{label, fields: [{fieldname, label, fieldtype, options,
  description, required, value, is_secret, is_set}]}]}`.
- `save_payment_integration(slug, enabled, values=None)` — POST. Returns one card. No screen in Comera's
  router currently targets this (no `/settings/payments` route exists yet).

### settings.py (11)
- `get_store_settings()` / `save_store_settings(**kwargs)` — `Lifestyle Settings` (`store_name,
  contact_email, contact_phone, working_hours, company`) + `Website Settings` branding (`brand_logo,
  footer_logo, favicon`).
- `get_shipping_settings()` / `save_shipping_settings(**kwargs)` — `{shipping_rule, return_period,
  reason_for_return: [{name, display_name, description}]}`.
- `get_payment_settings()` / `save_payment_settings(**kwargs)` — `{cod_enabled, cod_charge,
  cod_charge_applicable_below, charge_account_head}`.
- `get_footer_settings()` / `save_footer_settings(**kwargs)` — `{facebook_url, twitter_url, instagram_url,
  snapchat_url, tiktok_url, newsletter_title, newsletter_description, copyright_text,
  payment_methods_image, vat_certificate_image}`.
- `get_advanced_settings()` / `save_advanced_settings(**kwargs)` — meta-driven `Lifestyle Settings` field groups.
- `get_link_options(doctype, search_text=None)` — Returns `list[{label, value}]`.
- `get_profile()` / `save_profile(**kwargs)` — `User` self: `{name, email, full_name, first_name, last_name, user_image}`.
None of these have a corresponding Comera screen in the current router (no Settings section built yet).

### shipping.py (2)
- `get_shipping_integrations()` — System Manager only. Returns `list[card]` for `shiprocket, aftership`
  (same card shape as payments).
- `save_shipping_integration(slug, enabled, values=None)` — POST. Returns one card. No Comera route targets this yet.

---

## 4. Gap analysis

| Screen | Serving endpoint(s) | Shape match | Verdict | Notes |
|---|---|---|---|---|
| Dashboard `/` | `orders.get_overview` | Conceptually close (stats/recent/needs-attention) but `stats[]` ≠ `kpis[]` shape, `state{key,label}` ≠ `fulfillment` string, no `revenueByMonth` series anywhere | **ADAPT** | Chart series (`revenueByMonth`) is genuinely absent — `analytics.py` only holds tracking config, not aggregates |
| Orders `/orders` | `orders.get_orders` | Close — needs adapter for tab filters (unpaid/open/closed vs `status` enum) and `payment` vs `state` | **ADAPT** | Bulk "mark fulfilled" has no bulk endpoint (only single `fulfil_order`) |
| Order detail `/orders/:id` | `orders.get_order`, `orders.fulfil_order` | `get_order` matches well; `fulfil()` maps to `fulfil_order` | **ADAPT** | `refund()` and "Cancel order" have **no backend at all** — NEW |
| Products `/products` | `catalog.get_products`, `catalog.create_product` | Different unit of record: mock is flat products w/ `type`; catalog is Item-template + Style Attribute Variant options, no `productTypes`-style schema | **ADAPT** | "Import from CSV" flow — NEW |
| Product detail `/products/:id` | `catalog.get_product`, `update_product`, `save_product_prices`, `set_variant_published`, `add/remove_product_image` | Partial — pricing/publish/images map reasonably; **`typeFields`/`productTypes` schema has no backend equivalent** | **ADAPT** (core) + **NEW** (type fields) | See Product Types row below |
| Variant detail `/products/:id/variants/:id` | `catalog.save_product_prices`, `receive_product_stock`, `catalog.get_product` (sizes) | Reasonable fit for price/stock; `barcode`, `images` count are mock-only fields | **ADAPT** | |
| Collections `/collections` | `catalog.get_collections` | Endpoint returns `list[str]` (Item Group names) only — no `rule`, `count`, `condition` | **NEW** | Smart-collection rule engine does not exist in ls_shop; `Item Group` has no concept of a saved filter rule |
| Product Types `/product-types` | none | No endpoint or doctype models an arbitrary per-type field schema (author/language/pages...) | **NEW** — **verified: data model does not exist in ls_shop.** `Style Attribute Configurator` only carries `item_template`, `item_attribute` (option axis), `recommended_items` — nothing like a typed-field schema | |
| Attributes `/attributes` | `catalog.get_attribute_values` | Endpoint returns values for **one named attribute** only — no list-of-all-attributes-with-usage-count | **ADAPT** (values) + **NEW** (usage count, attribute list) | `Item Attribute` doctype exists in core Frappe/ERPNext and could back the list — usage counts would need a new aggregation |
| Inventory `/inventory` | `inventory.get_inventory` | Close, but no `locationId`/`location` (mock implies multi-location; ls_shop is single-warehouse via `Bin`) | **ADAPT** | `adjust()` bulk action has no backend — `inventory.receive_stock` only receives, no generic "adjust with reason" |
| Adjustments `/inventory/adjustments` | none | No endpoint returns a stock-movement ledger | **NEW** | Could be built off `Stock Ledger Entry` but no admin API surfaces it today |
| Pricing `/pricing` | `catalog.save_product_prices`, `catalog.get_products` (for row source) | Row list can adapt from `get_products`; **margin/cost has no backend field at all** (mock hardcodes 55% COGS client-side) | **ADAPT** (prices) + **NEW** (margin/cost data model — **verified absent**, no cost field found anywhere) | |
| Customers `/customers` | none | **No customer endpoint exists in `ls_shop/api/admin/*` at all** | **NEW** | ERPNext's core `Customer` doctype exists app-wide (referenced in `shipping.py`/`payments.py`) but nothing in `admin/` lists/aggregates it for a dashboard view |
| Customer detail `/customers/:id` | none | Same as above | **NEW** | |
| Analytics / Revenue | none | `analytics.py` is tracking-pixel config only, not a reporting endpoint | **NEW** | Could be built from `Sales Order` aggregation (same source `orders.get_overview` reads), but no existing endpoint returns a monthly series |
| Analytics / Inventory | none | No stock-value/dead-stock/sell-through aggregation endpoint exists | **NEW** | Buildable from `Bin` + `Item Price` + `Sales Order Item`, but ground-up |
| Analytics / Storefront | none | Sessions/channels/funnel/search-terms is **web analytics data (GA4/Meta pixel)**, not store data | **NEW**, and **verified out of ls_shop's own data model** — this requires calling out to GA4 Data API / Meta, using the credentials `analytics.py` already lets a merchant configure (`ga4_property_id`, `fb_pixel_id`) but does not itself fetch report data | |
| Storefront / Theme | none (config-adjacent: `settings.get_store_settings` for logos only) | `Shop Theme` / `Shop Theme Settings` / `Shop Themed Route` doctypes exist under `ls_shop/shop_themes/doctype/` but **no whitelisted admin endpoint reads or writes them** | **NEW** | Doctype scaffolding exists; API layer does not |
| Storefront / Navigation | `navigation.get_editor_data`, `add_node`, `update_node`, `delete_node`, `move_node`, `set_visibility`, `set_published` | Conceptually strong match (tree editor over `Ecommerce Category`) but node shape (`Ecommerce Category` fields) ≠ mock `{id, label, target, children}` | **ADAPT** | Best-covered NEW-adjacent screen — reuse this engine rather than building one |
| Storefront / Pages | none | No CMS-page listing/editing endpoint | **NEW** | No doctype found backing `title/slug/status/sections` as a generic page-builder record |

### Verified "does this exist in ls_shop at all" checks
- **Product Types** — confirmed **does not exist**. `Style Attribute Configurator` (the real product-schema
  doctype) has only `item_template`, `item_attribute`, `recommended_items` — no typed per-category field schema.
- **Pricing (margin/cost)** — confirmed **does not exist**. No cost field surfaced anywhere in `catalog.py`
  or its doctypes; the mock's 55%-COGS margin is a pure client-side fabrication.
- **Adjustments (ledger)** — the *concept* exists in core Frappe (`Stock Ledger Entry`) but **no admin API
  exposes it**; would be new API work over an existing core doctype, not a new doctype.
- **Storefront pages (Comera's three screens)** — Theme has doctype scaffolding but no API; Navigation has
  a strong existing engine (`navbar_manager`/`Ecommerce Category`); Pages (CMS) has neither doctype nor API.

### Build order
1. **Orders** (`get_orders`, `get_order`, `get_overview`, `fulfil_order`) — closest to READY/ADAPT, and
   Dashboard's KPI/recent-orders/needs-attention panels reuse the same reads. Wire this first so Dashboard
   inherits real data with minimal extra work.
2. **Catalog / Products / Variants / Inventory** (`catalog.py`, `inventory.py`) — the product/variant model
   underlies Pricing, Inventory, and Variant Detail; get this right once so those three don't diverge.
3. **Storefront Navigation** — reuse the existing `navbar_manager` engine; good ADAPT-tier win before
   tackling screens with no backend at all.
4. **New backend work, roughly in dependency order**: Customers (needed before Order Detail's customer
   panel can be fully real) → Collections rule engine → Attributes list/usage → Adjustments ledger →
   Analytics/Revenue and Analytics/Inventory (both derivable from Orders + Catalog once those are wired) →
   Analytics/Storefront (blocked on external GA4/Meta API integration, independent of the rest) →
   Product Types (only if the business actually wants typed per-category fields — confirm before building) →
   Pricing margin/cost (needs a product-level cost field decision first — money math, flag per house rule) →
   Storefront Theme and Storefront Pages (both need new doctypes/APIs from scratch, lowest priority /
   least de-risked by earlier work).
