import frappe
from webshop.webshop.doctype.webshop_settings.webshop_settings import (
    validate_cart_settings,
)


def execute(doc, method=None):
    """
    Check if Price List currency change impacts Webshop Cart
    """
    if doc.is_new():
        return

    doc_before_save = doc.get_doc_before_save()
    currency_changed = doc.currency != doc_before_save.currency
    affects_cart = doc.name == frappe.get_cached_value(
        "Webshop Settings", None, "price_list"
    )

    if currency_changed and affects_cart:
        validate_cart_settings()
