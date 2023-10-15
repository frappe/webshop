import frappe
from frappe import _
from frappe.utils import cint


def execute(doc, method=None):
    """
    If shopping cart is enabled and no tax rule exists for shopping cart, enable this one
    """
    if doc.use_for_shopping_cart:
        return

    is_enabled = cint(frappe.db.get_single_value("Webshop Settings", "enabled"))

    if not is_enabled:
        return

    use_for_cart = frappe.db.get_value(
        "Tax Rule", {"use_for_shopping_cart": 1, "name": ["!=", doc.name]}
    )

    if not use_for_cart:
        return

    doc.use_for_shopping_cart = 1

    frappe.msgprint(
        _(
            """
            Enabling 'Use for Shopping Cart', as Shopping Cart is enabled
            and there should be at least one Tax Rule for Shopping Cart
            """
        )
    )
