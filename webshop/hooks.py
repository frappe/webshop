from . import __version__ as _version

app_name = "webshop"
app_title = "Webshop"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Open Source eCommerce Platform"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
app_version = _version

required_apps = ["payments", "erpnext"]

web_include_css = ["webshop-web.bundle.css", "/assets/webshop/css/webshop-modern.css"]

web_include_js = "web.bundle.js"

after_install = "webshop.setup.install.after_install"
on_logout = "webshop.webshop.shopping_cart.utils.clear_cart_count"
on_session_creation = [
    "webshop.webshop.utils.portal.update_debtors_account",
    "webshop.webshop.shopping_cart.utils.set_cart_count",
]
update_website_context = [
    "webshop.webshop.shopping_cart.utils.update_website_context",
]

website_generators = ["Website Item", "Item Group"]

website_redirects = [
    {"source": "/index", "target": "/"},
    {"source": "/products/freshmate", "target": "/storage/freshmate"},
]

override_doctype_class = {
    "Payment Request": "webshop.webshop.doctype.override_doctype.payment_request.PaymentRequest",
    "Item Group": "webshop.webshop.doctype.override_doctype.item_group.WebshopItemGroup",
    "Item": "webshop.webshop.doctype.override_doctype.item.WebshopItem",
}

doctype_js = {
    "Item": "public/js/override/item.js",
    "Homepage": "public/js/override/homepage.js",
}

doc_events = {
    "Item": {
        "on_update": [
            "webshop.webshop.crud_events.item.update_website_item.execute",
            "webshop.webshop.crud_events.item.invalidate_item_variants_cache.execute",
        ],
        "before_rename": [
            "webshop.webshop.crud_events.item.validate_duplicate_website_item.execute",
        ],
        "after_rename": [
            "webshop.webshop.crud_events.item.invalidate_item_variants_cache.execute",
        ],
    },
    "Sales Taxes and Charges Template": {
        "on_update": [
            "webshop.webshop.doctype.webshop_settings.webshop_settings.validate_cart_settings",
        ],
    },
    "Quotation": {
        "validate": [
            "webshop.webshop.crud_events.quotation.validate_shopping_cart_items.execute",
        ],
    },
    "Price List": {
        "validate": [
            "webshop.webshop.crud_events.price_list.check_impact_on_cart.execute"
        ],
    },
    "Tax Rule": {
        "validate": [
            "webshop.webshop.crud_events.tax_rule.validate_use_for_cart.execute",
        ],
    },
}

scheduler_events = {
    "hourly": [
        "webshop.webshop.engagement.send_abandoned_cart_reminders",
    ]
}


has_website_permission = {
    "Website Item": "webshop.webshop.doctype.website_item.website_item.has_website_permission_for_website_item",
    "Item Group": "webshop.webshop.doctype.website_item.website_item.has_website_permission_for_item_group"
}

custom_fields = {
    "Sales Order": [
        {
            "fieldname": "payment_method",
            "label": "Payment Method",
            "fieldtype": "Data",
            "insert_after": "payment_gateway_account",
            "read_only": 1,
            "in_list_view": 1
        },
        {
            "fieldname": "payment_review_section",
            "label": "Webshop Payment Review",
            "fieldtype": "Section Break",
            "insert_after": "payment_method",
            "collapsible": 1
        },
        {
            "fieldname": "requires_payment_review",
            "label": "Requires Payment Review",
            "fieldtype": "Check",
            "insert_after": "payment_review_section",
            "read_only": 1,
            "in_list_view": 1
        },
        {
            "fieldname": "payment_review_status",
            "label": "Payment Review Status",
            "fieldtype": "Select",
            "options": "\nPending Verification\nApproved\nRejected",
            "insert_after": "requires_payment_review",
            "read_only": 1,
            "in_list_view": 1
        },
        {
            "fieldname": "payment_receipt",
            "label": "Payment Receipt",
            "fieldtype": "Attach",
            "insert_after": "payment_review_status",
            "read_only": 1
        },
        {
            "fieldname": "payment_review_notes",
            "label": "Payment Review Notes",
            "fieldtype": "Small Text",
            "insert_after": "payment_receipt"
        },
        {
            "fieldname": "payment_review_column_break",
            "fieldtype": "Column Break",
            "insert_after": "payment_review_notes"
        },
        {
            "fieldname": "payment_reviewed_by",
            "label": "Payment Reviewed By",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "payment_review_column_break",
            "read_only": 1
        },
        {
            "fieldname": "payment_reviewed_on",
            "label": "Payment Reviewed On",
            "fieldtype": "Datetime",
            "insert_after": "payment_reviewed_by",
            "read_only": 1
        }
    ],
    "Webshop Settings": [
        {
            "fieldname": "conversion_section",
            "label": "Conversion Boosters",
            "fieldtype": "Section Break",
            "insert_after": "redirect_on_action",
            "collapsible": 1
        },
        {
            "fieldname": "delivery_promise_text",
            "label": "Delivery Promise Text",
            "fieldtype": "Data",
            "insert_after": "conversion_section",
            "default": "Delivery in 2-4 working days"
        },
        {
            "fieldname": "returns_promise_text",
            "label": "Returns / Support Promise Text",
            "fieldtype": "Data",
            "insert_after": "delivery_promise_text",
            "default": "Easy exchange and support after purchase"
        },
        {
            "fieldname": "first_order_coupon_code",
            "label": "First Order Coupon Code",
            "fieldtype": "Data",
            "insert_after": "returns_promise_text"
        },
        {
            "fieldname": "first_order_coupon_text",
            "label": "First Order Coupon Text",
            "fieldtype": "Data",
            "insert_after": "first_order_coupon_code",
            "default": "Use this code on your first order"
        },
        {
            "fieldname": "conversion_column_break",
            "fieldtype": "Column Break",
            "insert_after": "first_order_coupon_text"
        },
        {
            "fieldname": "low_stock_threshold",
            "label": "Low Stock Threshold",
            "fieldtype": "Int",
            "insert_after": "conversion_column_break",
            "default": "5"
        },
        {
            "fieldname": "enable_exit_intent_recovery",
            "label": "Enable Exit Intent Cart Recovery",
            "fieldtype": "Check",
            "insert_after": "low_stock_threshold",
            "default": "1"
        }
    ]
}
