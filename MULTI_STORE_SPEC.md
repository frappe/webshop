# Webshop Multi‑Store (Warehouse‑Based) Spec

## Summary

Single company + multiple warehouses with a per‑store price list. The website exposes a store picker that persists the selected store and ensures that prices, stock availability, cart, and checkout consistently respect the selected store’s Warehouse and Price List. No multi‑company and no payment gateway changes for the demo.

## Goals

- Store selection UX that maps to a Warehouse and a Price List
- Store‑aware pricing in listing and PDP, including Warehouse‑scoped Pricing Rules
- Store‑aware stock indicators for listing and PDP
- Cart lines and order placement set the selected Warehouse; cart totals use the selected Price List
- Correct caching behavior for store‑dependent pages
- Minimal, isolated changes in Webshop (no ERPNext core changes)

## Non‑Goals (for demo)

- Windcave or additional payment gateways
- Multi‑company checkout
- SEO/store‑specific routes beyond basic cache handling

## Terminology

- Store: A frontend concept mapping to a Warehouse and a Price List
- Warehouse: ERPNext Stock location used per store for stock and Warehouse‑scoped Pricing Rules
- Price List: ERPNext selling price list used per store for price display and cart totals
- Store cookie/session: `{ store_slug, store_warehouse, store_price_list }`

---

## Data Model

New DocType: Website Store
- Fields
  - `store_name (Data, reqd)`
  - `slug (Data, unique, reqd)`
  - `warehouse (Link: Warehouse, reqd)`
  - `price_list (Link: Price List, reqd)`
  - `cost_center (Link: Cost Center, optional)`
  - `hero_image (Attach, optional)`
  - `store_description (Small Text, optional)`
  - `sort_order (Int, optional)`
  - `is_published (Check, default=1)`
  - `disabled (Check, default=0)`
- Location: `webshop/webshop/doctype/website_store/`
- Purpose: Central, reusable mapping for UI and server logic

Validation
- Ensure warehouse and price list are valid for the same company context; enforce a single selling currency across stores for the demo (or document multi‑currency as out of scope).

Reporting
- Add optional Link fields `website_store` on Quotation and Sales Order for per‑store reporting.

Defaults
- Add `default_website_store` in Webshop Settings to resolve the active store when cookie is absent.

---

## Store Picker UX

- Navbar dropdown: “Choose Store” listing published `Website Store` records
- On selection, call backend to persist cookies and reload
- Visual indicator of the active store in the header

Files to touch
- `apps/webshop/webshop/templates/includes/navbar/navbar_items.html` (inject dropdown)
- `apps/webshop/webshop/public/web.bundle.js` (import picker JS)
- New: `apps/webshop/webshop/public/js/store_picker.js` (handles selection + API calls)

UI details
- Use a `<select>` or dropdown button labeled “Choose Store”.
- Disable control and show a small spinner while switching; on API failure, toast an error and revert selection.

Build
- Run `bench build` after adding the new JS module to the bundle.

---

## Backend: Store API + Context

Endpoints (frappe.whitelist, allow_guest=True)
- `webshop.webshop.api.store.list_stores()`
  - Returns `[ {slug, store_name, description, sort_order} ]` of published Website Store records
- `webshop.webshop.api.store.get_active_store()`
  - Reads cookies (`store_slug`); resolves to `Website Store` (fallback to default)
- `webshop.webshop.api.store.set_active_store(slug)`
  - Validates slug; sets cookies: `store_slug`, `store_warehouse`, `store_price_list`
  - Optionally re‑applies cart settings (see Cart section)

Module structure
- Create `apps/webshop/webshop/webshop/api/` with `__init__.py` and `store.py`. Whitelisted endpoints are invoked by dotted path; no hooks entries are required.

API response contract
- list_stores: `{ stores: [ { slug, name, description, sort_order } ] }`
- get_active_store: `{ store: { slug, name, warehouse, price_list } }`
- set_active_store: `{ ok: true, store: { slug, name, warehouse, price_list } }` (or `{ ok: false, error: str }`)

Context hook
- Extend `update_website_context(context)` in `apps/webshop/webshop/webshop/shopping_cart/utils.py` to inject:
  - `context.stores` (published Website Stores for header)
  - `context.current_store` (resolved store)
  - Applies globally so PDP, listing, cart, and navbar can all access the active store.

Cookie helper
- New utility to consistently read cookies and provide a fallback:
  - `get_store_from_cookies() -> {slug, warehouse, price_list}`

## Cookies & Session

- Cookies: set `Secure` (HTTPS), `SameSite=Lax`, and a 30‑day expiry. `HttpOnly` is not set if the UI needs to read the cookie; server always validates.
- If cookies are cleared mid‑session: fall back to `default_website_store` or single‑store behavior; show a subtle notification on the next action.
- Guests can select a store. On login, preserve the selection and re‑apply cart settings.

---

## Pricing (Listing + PDP)

Problem
- `erpnext.utilities.product.get_price(...)` does not pass `warehouse` into the pricing rule engine. Warehouse‑scoped Pricing Rules won’t fire unless `args.warehouse` is set downstream.

Solution
- New helper: `webshop.webshop.utils.pricing.get_price_for_store(...)`
  - Inputs: `item_code, price_list, warehouse, company, customer_group, party=None, qty=1`
  - Logic: replicate minimal `get_price` logic, but call `get_pricing_rule_for_item(pricing_rule_dict)` with `pricing_rule_dict["warehouse"] = warehouse` so Warehouse‑scoped rules apply. Preserve formatted outputs (formatted_price, formatted_mrp, formatted_price_sales_uom, etc.).

Alternative
- Consider an upstream patch (or targeted monkey‑patch) to allow passing `warehouse` to core `get_price`. For the demo, proceed with the wrapper while noting duplication risk.

Wire‑up
- PDP price
  - File: `apps/webshop/webshop/webshop/shopping_cart/product_info.py`
  - Replace `get_price(...)` with `get_price_for_store(...)` using `price_list` and `warehouse` from cookies; keep party/company/customer_group as is.
- Listing price
  - File: `apps/webshop/webshop/webshop/product_data_engine/query.py`
  - `add_display_details()` calls `get_product_info_for_website(...)` already; no direct change here once PDP path is store‑aware.
- Wishlist price
  - File: `apps/webshop/webshop/templates/pages/wishlist.py`
  - Replace direct `get_price(...)` with `get_price_for_store(...)` using cookie `store_price_list` and `store_warehouse`.

Acceptance
- Given a Pricing Rule scoped to Warehouse A, selecting Store A (Warehouse A) changes PDP and listing prices accordingly; switching to Store B reflects Warehouse B’s rules.

---

## Stock Indicator (Listing + PDP)

- Listing stock
  - File: `apps/webshop/webshop/webshop/product_data_engine/query.py`
    - Method `get_stock_availability(self, item)` imports `get_stock_availability` from wishlist and passes `website_warehouse`.
  - File: `apps/webshop/webshop/templates/pages/wishlist.py`
    - Update `get_stock_availability(item_code, warehouse)` to prefer cookie `store_warehouse` if present (handles group warehouses via `get_child_warehouses`). This change makes ProductQuery listing stock store‑aware without further changes.
- PDP stock
  - File: `apps/webshop/webshop/webshop/shopping_cart/product_info.py`
    - Replace `get_web_item_qty_in_stock(item_code, "website_warehouse")` with `get_web_item_qty_in_stock(item_code, "website_warehouse", warehouse=cookie.store_warehouse)`.
    - For non‑stock bundles via `get_non_stock_item_status(...)`, also pass the cookie warehouse as context.

Variants
- Ensure template/variant resolution in `get_web_item_qty_in_stock` consults the cookie warehouse (not only item’s Website Item setting).

Acceptance
- With Store A selected, stock badges and quantities reflect only Warehouse A (or its children if a group warehouse is configured).

---

## Cart & Checkout Coherence

- Add to cart (Quotation Item.warehouse)
  - File: `apps/webshop/webshop/webshop/shopping_cart/cart.py`
  - In `update_cart(...)`, replace `warehouse = Website Item.website_warehouse` with cookie `store_warehouse`.
- Quotation price list
  - File: `apps/webshop/webshop/webshop/shopping_cart/cart.py`
  - In `_set_price_list(...)`, prefer cookie `store_price_list` if set; else fallback to Customer default or `Webshop Settings.price_list`.
- Place order validation
  - File: `apps/webshop/webshop/webshop/shopping_cart/cart.py`
  - In `place_order()`, set `item.warehouse` using cookie `store_warehouse` and validate stock using the same warehouse via `get_web_item_qty_in_stock(..., warehouse=cookie.store_warehouse)` when `allow_items_not_in_stock` is false. Do not overwrite with Website Item’s `website_warehouse` when multi‑store is enabled.
- Store change behavior
  - Endpoint: `set_active_store(slug)`
  - After setting cookies, if a cart exists, call `apply_cart_settings()` to re‑apply quotation `selling_price_list`, rates, and totals under the new store.

Atomicity & validation
- Wrap store switch + cart recalculation in a transaction; validate each line against the new store’s warehouse. For unavailable items, annotate and prompt removal instead of silently clearing.

Website Item warehouse references
- Where web/cart code sets line `warehouse` from `Website Item.website_warehouse` (e.g., `decorate_quotation_doc`), prefer the cookie warehouse when multi‑store is enabled.

Acceptance
- Cart lines carry the selected store’s warehouse; totals reflect the selected store’s price list. Switching store updates totals and subsequent line warehouses.

---

## Caching & Variants

- Current pages already disable cache:
  - Listing: `apps/webshop/webshop/www/all-products/index.py` sets `context.no_cache = 1`
  - PDP: `WebsiteItem.website.no_cache = 1` in `apps/webshop/webshop/webshop/doctype/website_item/website_item.py`
  - Item Groups: `apps/webshop/webshop/webshop/doctype/override_doctype/item_group.py` sets `no_cache=1`
- For future performance (outside demo): add vary‑by `store_slug` cookie for product/listing routes if global cache is re‑enabled.

Store‑aware caching
- Add Redis caches (3–5 minutes TTL) for store‑specific price and stock keyed by `{store_slug,item_code}` to reduce per‑item queries on listing pages.

---

## Edge Cases & Fallbacks

- No active store cookie: resolve to `default_website_store` (Webshop Settings) or fallback to single‑store behavior
- Item has no price in selected store’s price list: show base list price (if configured) with a badge “Store price not set” and optionally disable add‑to‑cart
- Zero stock in selected warehouse but stock elsewhere: optionally show “Available at other stores” hint (informational only for demo)
- Unpublished/disabled Website Store: prevent selection and show a friendly error; if the cookie points to an invalid store, reset to default.
- Guest → login: preserve the selected store and re‑apply cart settings.

---

## Admin UX Notes

- Maintain per‑store Item Prices under each store’s Price List (Option A), or use Pricing Rules with Warehouse condition (Option B) when most prices are shared
- Website Store records are the single source of truth for the Store ↔ Warehouse/Price List mapping
 - Optional: Use Website Store’s `cost_center` on Sales Orders created from that store for accounting alignment.

## Settings & Toggle

- Webshop Settings additions:
  - `enable_multi_store (Check)` toggles multi‑store behavior; when off, hide store picker, clear store cookies, and behave as single‑store (global website warehouse + price list).
  - `default_website_store (Link: Website Store)` is used to resolve the active store when cookies are missing/invalid.

---

## File‑Level Task List

Data & API
- [ ] Add DocType `Website Store`: `apps/webshop/webshop/webshop/doctype/website_store/` (json, py, list)
- [ ] Add API module and endpoints: `apps/webshop/webshop/webshop/api/{__init__.py, store.py}` with `list_stores`, `get_active_store`, `set_active_store` (return JSON as per contract)
- [ ] Add cookie helper util: `get_store_from_cookies()`
- [ ] Webshop Settings: add `enable_multi_store` and `default_website_store`

Context
- [ ] Extend `update_website_context(context)` in `apps/webshop/webshop/webshop/shopping_cart/utils.py` to add `stores` and `current_store`

Frontend
- [ ] Navbar dropdown in `apps/webshop/webshop/templates/includes/navbar/navbar_items.html`
- [ ] New `apps/webshop/webshop/public/js/store_picker.js` and import in `apps/webshop/webshop/public/web.bundle.js` (run `bench build`)

Pricing
- [ ] New helper: `apps/webshop/webshop/webshop/utils/pricing.py` with `get_price_for_store`
- [ ] Use in `apps/webshop/webshop/webshop/shopping_cart/product_info.py` (replace `get_price` calls)
- [ ] Use in `apps/webshop/webshop/templates/pages/wishlist.py`

Stock
- [ ] Update `apps/webshop/webshop/templates/pages/wishlist.py:get_stock_availability(...)` to respect cookie warehouse
- [ ] Update `apps/webshop/webshop/webshop/shopping_cart/product_info.py` to pass cookie warehouse to `get_web_item_qty_in_stock` and `get_non_stock_item_status`

Cart & Checkout
- [ ] In `apps/webshop/webshop/webshop/shopping_cart/cart.py:update_cart(...)` use cookie `store_warehouse` for line `warehouse`
- [ ] In `apps/webshop/webshop/webshop/shopping_cart/cart.py:_set_price_list(...)` prefer cookie `store_price_list`
- [ ] In `apps/webshop/webshop/webshop/shopping_cart/cart.py:place_order()` set/validate by cookie `store_warehouse` (do not overwrite with Website Item warehouse)
- [ ] Update `decorate_quotation_doc` to not inject Website Item warehouse when multi‑store is enabled
- [ ] In `set_active_store`, wrap in transaction and call `apply_cart_settings()`; flag items unavailable in new store

Theme & Messaging (demo polish)
- [ ] Website Theme for brand colors/fonts (site config)
- [ ] Add “Prices exclude GST” suffix in PDP/listing templates where appropriate
- [ ] Optional: Badge when store price missing; friendly error messages for invalid store, no store price, and OOS

---

## Acceptance Tests (Manual for Demo)

1) Store selection
- Select Store A; header shows active store name
- Reload persists selection

2) Pricing
- PDP shows Store A price; switching to Store B updates price
- Listing tiles show Store price consistently with PDP
- Pricing Rule scoped to Warehouse A only applies when Store A is active
 - Single selling currency is enforced (or multi‑currency clearly out of scope).

3) Stock
- PDP “In stock”/quantity reflects only selected Warehouse
- Listing stock badges match PDP

4) Cart
- Add item; Quotation Item.warehouse equals selected store warehouse
- Cart totals reflect store price list; switching store then re‑loading the cart recomputes totals
 - Items unavailable in new store are flagged with option to remove.

5) Checkout
- Place order with allow_items_not_in_stock disabled: stock validation happens against the selected warehouse
 - Sales Order captures `website_store` and optional `cost_center` from Website Store.

6) Fallbacks
- No cookie: default store applied
- Item with no store price: base price shown with “Store price not set” badge (if configured)
 - Invalid/unpublished store cookie resets to default with message.

---

## Risks & Mitigations

- Pricing Rule interplay: ensure `warehouse` is passed to the rule engine via the wrapper
- Caching: keep no_cache for PDP/listing during demo; later add vary‑by cookie
- Cart switching stores: re‑apply cart settings after store change; document behavior

---

## Testing Strategy

- Unit tests: pricing helper outputs (formatted values, discounts) under store contexts
- Integration: store switching with cart reprice, stock validation per store, wishlist/listing stock badges
- Fixtures: two Website Stores with distinct warehouses and price lists
- Perf smoke: listing with 24 items and store‑aware caching on

## Build & Deployment

- After adding `store_picker.js` or other assets, run `bench build`.
- Ensure API dotted paths resolve; whitelisted methods do not need additional hooks entries.

## Roll‑Out & Toggle

- Optional flag: `Enable Multi‑Store Storefront` (Checkbox) in `Webshop Settings` to activate store picker and store‑aware logic; when off, hide store picker, clear store cookies, and behave as single‑store (global website warehouse + price list).

## Migration

- For existing open carts/quotations, set `website_store` and re‑apply pricing on next cart interaction by resolving to `default_website_store`.
- No historical data migration required; reporting can use warehouses retroactively.

## Future Work

- Store locator page (addresses, contact) sourced from `Website Store`
- SEO: store‑aware metadata (if needed)
- Tax templates or shipping rules varying by store
- Soft reservation across stores (out of scope for demo; rely on validation at checkout)
