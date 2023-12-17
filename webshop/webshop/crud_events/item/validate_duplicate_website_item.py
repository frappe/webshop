import frappe

from frappe import _
from frappe.utils import get_link_to_form


class DataValidationError(frappe.ValidationError):
    pass


def execute(doc, method=None, old_name=None, new_name=None, merge=False):
    """
    Block merge if both old and new items have website items against them.
    This is to avoid duplicate website items after merging.
    """
    if not merge:
        return

    web_items = frappe.get_all(
        "Website Item",
        filters={"item_code": ["in", [old_name, new_name]]},
        fields=["item_code", "name"],
    )

    if len(web_items) <= 1:
        return

    old_web_item = [d.get("name") for d in web_items if d.get("item_code") == old_name][0]
    web_item_link = get_link_to_form("Website Item", old_web_item)
    old_name, new_name = frappe.bold(old_name), frappe.bold(new_name)

    msg = f"Please delete linked Website Item {frappe.bold(web_item_link)} before merging {old_name} into {new_name}"
    frappe.throw(_(msg), title=_("Cannot Merge"), exc=DataValidationError)

