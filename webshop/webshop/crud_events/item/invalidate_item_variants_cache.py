import frappe
from webshop.webshop.variant_selector.item_variants_cache import (
    ItemVariantsCacheManager,
)


def execute(doc, method=None, old_name=None, new_name=None, merge=False):
    """
    Rebuild ItemVariantsCacheManager via Item or Website Item.
    """
    item_code = None
    is_web_item = doc.get("published_in_website") or doc.get("published")
    is_published = frappe.db.get_value("Item", doc.variant_of, "published_in_website")

    if doc.has_variants and is_web_item:
        item_code = doc.item_code

    elif doc.variant_of and is_published:
        item_code = doc.variant_of

    if item_code:
        item_cache = ItemVariantsCacheManager(item_code)
        item_cache.rebuild_cache()
