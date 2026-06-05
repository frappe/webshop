# apps/webshop/webshop/api/search.py

import frappe
from frappe import _
import json
from frappe.utils.data import flt

@frappe.whitelist(allow_guest = True)
def product_search(q):
	if not q:
		return []

	or_filters = [
		["item_code", "like", f"%{q}%"],
		["item_name", "like", f"%{q}%"],
		["web_long_description", "like", f"%{q}%"],
		["web_item_name", "like", f"%{q}%"]
	]

	raw_items = frappe.get_all(
		"Website Item",
		fields=["name", "item_code", "item_name", "item_group", "website_image", "web_item_name", "route"],
		or_filters=or_filters,
		filters={"published": 1},
		limit_page_length=20
	)

	hide_unavailable = frappe.db.get_single_value("Webshop Settings", "hide_unavailable_items") or 0

	visible_items = []

	for item in raw_items:
		item_doc = frappe.get_doc("Item", item.item_code)

		warehouse = frappe.db.get_value("Website Item", item.name, "website_warehouse") or \
		            frappe.db.get_single_value("Stock Settings", "default_warehouse")

		actual_qty = 0
		if item.item_code and warehouse:
			actual_qty = frappe.db.get_value("Bin", {
				"item_code": item.item_code,
				"warehouse": warehouse
			}, "actual_qty") or 0

		updated_item = item.copy()
		updated_item.update({
			"stock_qty": flt(actual_qty),
			"in_stock": actual_qty > 0,
			"is_stock": item_doc.is_stock_item,
			"on_backorder": item_doc.delivered_by_supplier,
			"has_variants": item_doc.has_variants
		})

		if hide_unavailable:
			if updated_item["in_stock"] or updated_item["on_backorder"]:
				visible_items.append(updated_item)
		else:
			visible_items.append(updated_item)

	return visible_items