# apps/webshop/webshop/api/product_search.py

import frappe
from frappe import _

@frappe.whitelist()
def product_search(q):
	if not q:
		return []

	or_filters = [
		["item_code", "like", f"%{q}%"],
		["item_name", "like", f"%{q}%"],
		["web_long_description", "like", f"%{q}%"],
		["web_item_name", "like", f"%{q}%"]
	]

	return frappe.get_all(
		"Website Item",
		fields=["name", "item_code", "item_name", "item_group", "website_image", "web_item_name", "route"],
		or_filters=or_filters,
		filters={"published": 1},
		limit_page_length=20
	)