from . import __version__ as _version

app_name = "shop"
app_title = "Shop"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Open Source eCommerce Platform"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
app_version = _version

required_apps = ["payments", "erpnext"]

web_include_css = "shop-web.bundle.css"

web_include_js = "web.bundle.js"

after_install = "shop.setup.install.after_install"
on_logout = "shop.shop.shopping_cart.utils.clear_cart_count"
on_session_creation = [
    "shop.shop.utils.portal.update_debtors_account",
    "shop.shop.shopping_cart.utils.set_cart_count",
]
update_website_context = [
    "shop.shop.shopping_cart.utils.update_website_context",
]

website_generators = ["Website Item", "Item Group"]

override_doctype_class = {
    "Payment Request": "shop.shop.doctype.override_doctype.payment_request.PaymentRequest",
    "Item Group": "shop.shop.doctype.override_doctype.item_group.ShopItemGroup",
    "Item": "shop.shop.doctype.override_doctype.item.ShopItem",
}

doctype_js = {
    "Item": "public/js/override/item.js",
    "Homepage": "public/js/override/homepage.js",
}

doc_events = {
    "Item": {
        "on_update": [
            "shop.shop.crud_events.item.update_website_item.execute",
            "shop.shop.crud_events.item.invalidate_item_variants_cache.execute",
        ],
        "before_rename": [
            "shop.shop.crud_events.item.validate_duplicate_website_item.execute",
        ],
        "after_rename": [
            "shop.shop.crud_events.item.invalidate_item_variants_cache.execute",
        ],
    },
    "Sales Taxes and Charges Template": {
        "on_update": [
            "shop.shop.doctype.shop_settings.shop_settings.validate_cart_settings",
        ],
    },
    "Quotation": {
        "validate": [
            "shop.shop.crud_events.quotation.validate_shopping_cart_items.execute",
        ],
    },
    "Price List": {
        "validate": [
            "shop.shop.crud_events.price_list.check_impact_on_cart.execute"
        ],
    },
    "Tax Rule": {
        "validate": [
            "shop.shop.crud_events.tax_rule.validate_use_for_cart.execute",
        ],
    },
}

has_website_permission = {
    "Website Item": "shop.shop.doctype.website_item.website_item.has_website_permission_for_website_item",
    "Item Group": "shop.shop.doctype.website_item.website_item.has_website_permission_for_item_group"
}
