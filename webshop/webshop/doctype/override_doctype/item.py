import frappe
from frappe import _
from frappe.utils import get_link_to_form
from erpnext.stock.doctype.item.item import Item
from webshop.webshop.doctype.override_doctype.item_group import invalidate_cache_for

class DataValidationError(frappe.ValidationError):
	pass

class WebshopItem(Item):
	def on_update(self):
		super(WebshopItem, self).on_update()
		invalidate_cache_for_item(self)
		super(WebshopItem, self).on_update()

	def before_rename(self, old_name, new_name, merge=False):
		self.validate_duplicate_website_item_before_merge(old_name, new_name)
		return super(WebshopItem, self).before_rename(old_name, new_name, merge)

	def validate_duplicate_website_item_before_merge(self, old_name, new_name):
		"""
		Block merge if both old and new items have website items against them.
		This is to avoid duplicate website items after merging.
		"""
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

	def after_rename(self, old_name, new_name, merge):
		if self.published_in_website:
			invalidate_cache_for_item(self)

		super(WebshopItem, self).after_rename(old_name, new_name, merge)


def invalidate_cache_for_item(doc):
	"""Invalidate Item Group cache and rebuild ItemVariantsCacheManager."""
	invalidate_cache_for(doc, doc.item_group)

	if doc.get("old_item_group") and doc.get("old_item_group") != doc.item_group:
		invalidate_cache_for(doc, doc.old_item_group)
