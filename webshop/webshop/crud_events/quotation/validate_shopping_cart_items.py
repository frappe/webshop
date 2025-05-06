import frappe
from frappe import _


def execute(doc, method=None):
    if doc.order_type != "Shopping Cart":
        return

    webshop_settings = frappe.get_cached_doc("Webshop Settings")
    for item in doc.items:
        has_web_item = frappe.db.exists("Website Item", {"item_code": item.item_code})

        # If variant is unpublished but template is published: valid
        template = frappe.get_cached_value("Item", item.item_code, "variant_of")
        if template and not has_web_item:
            has_web_item = frappe.db.exists("Website Item", {"item_code": template})

        if not has_web_item and not webshop_settings.allow_non_website_items_in_cart_quotation:
            frappe.throw(
                _(
                    "Row #{0}: Item {1} must have a Website Item for Shopping Cart Quotations"
                ).format(item.idx, frappe.bold(item.item_code)),
                title=_("Unpublished Item"),
            )
