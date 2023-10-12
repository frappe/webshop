import frappe
from erpnext.stock.doctype.item.item import Item
from webshop.webshop.doctype.override_doctype.item_group import invalidate_cache_for


class WebshopItem(Item):
	def on_update(self):
		invalidate_cache_for_item(self)


def invalidate_cache_for_item(doc):
	"""Invalidate Item Group cache and rebuild ItemVariantsCacheManager."""
	invalidate_cache_for(doc, doc.item_group)

	if doc.get("old_item_group") and doc.get("old_item_group") != doc.item_group:
		invalidate_cache_for(doc, doc.old_item_group)