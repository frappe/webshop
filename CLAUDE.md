# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Frappe Webshop is an open-source eCommerce platform built on the Frappe framework. It integrates with ERPNext for inventory, billing, and order processing. The app is developed primarily in Python (backend) and JavaScript (frontend), with Jinja templates for web pages.

## Common Development Tasks

### Environment Setup

This is a Frappe app that must be installed within a Bench environment. The typical setup involves:

1. **Install Bench**: `pip install frappe-bench`
2. **Initialize Bench**: `bench init --frappe-branch develop --skip-redis-config-generation --skip-assets ~/frappe-bench`
3. **Install dependencies**: `bench setup requirements --dev`
4. **Get required apps**: `bench get-app erpnext --branch develop`, `bench get-app payments --branch develop`
5. **Get webshop app**: `bench get-app /path/to/webshop`
6. **Create site**: `bench new-site --db-root-password root --admin-password admin test_site`
7. **Install apps on site**: `bench --site test_site install-app erpnext`, `bench --site test_site install-app webshop`
8. **Build assets**: `bench build`

### Running Tests

Tests use Python's unittest framework and are executed via Bench:

```bash
bench --site test_site set-config allow_tests true
bench --site test_site run-tests --app webshop
```

To run a specific test file:
```bash
bench --site test_site run-tests --app webshop --doctype "Website Item"
```

### Code Quality

- **Black formatting**: Line length 99, configured in `pyproject.toml`
- **isort**: Also configured in `pyproject.toml`
- **No pre-commit hooks** are defined in the repository

### Frontend Assets

Frontend assets (JavaScript, CSS) are bundled via Frappe's asset pipeline. After making changes to JS/CSS files, run `bench build` to rebuild bundles.

## High-Level Architecture

### Frappe App Structure

- `webshop/` – Root app directory
  - `hooks.py` – App configuration, doctype overrides, web includes, and event handlers
  - `webshop/` – Main Python module
    - `doctype/` – Custom DocTypes (Website Item, Webshop Settings, Wishlist, Item Review, etc.)
    - `override_doctype/` – Overrides for ERPNext DocTypes (Item, Item Group, Payment Request)
    - `product_data_engine/` – Query engine for product listing and filtering
    - `shopping_cart/` – Cart and checkout utilities
    - `utils/` – Product, portal, and setup utilities
    - `web_template/` – Reusable website components (product card, hero slider, etc.)
    - `variant_selector/` – Item variant selection logic and caching
  - `public/` – Static assets (JS, CSS, images)
  - `www/` – Website pages (shop-by-category, all-products)
  - `templates/` – Jinja templates for web pages

### Key Components

1. **Product Data Engine** (`product_data_engine/`): Handles product queries, filtering, and search. Uses `ProductQuery` and `ProductFiltersBuilder` classes.

2. **Shopping Cart** (`shopping_cart/`): Manages cart operations, product info, and cart count updates.

3. **Website Item**: Custom DocType that extends ERPNext Item with e‑commerce fields (published status, website image, etc.). The `website_item` module also provides permission hooks.

4. **Webshop Settings**: Singleton DocType for configuring store behavior (products per page, filters, cart settings).

5. **Web Templates**: Reusable UI components built with Frappe's Web Template feature. Each template has HTML, JSON config, and Python controller.

6. **API Endpoints**: Whitelisted functions in `api.py` provide product filter data and guest redirects.

### Integration Points

- **ERPNext**: Required app. Webshop overrides Item, Item Group, and Payment Request DocTypes.
- **Payments**: Required app for payment processing.
- **Frappe Website**: Uses Frappe's website generator for routes, context, and permission handling.

### Event Hooks

See `hooks.py` for detailed event registrations:
- `doc_events`: Item updates, Quotation validation, Tax Rule validation, etc.
- `override_doctype_class`: Overrides for Payment Request, Item Group, Item
- `has_website_permission`: Custom permission checks for Website Item and Item Group
- `update_website_context`: Cart count updates
- `after_install`, `on_logout`, `on_session_creation` hooks

## Dependencies

- **Required Apps**: `payments`, `erpnext` (must be installed before webshop)
- **Python**: >=3.10
- **Frappe Bench**: For development and deployment

## Notes

- The app version is defined in `webshop/__init__.py` (currently 16.0.0).
- The CI pipeline (`.github/workflows/ci.yml`) runs tests using the commands listed above.
- Frontend JavaScript overrides for Item and Homepage are registered in `hooks.py` (`doctype_js`).