import json
from typing import List, Union

import frappe

from webshop.webshop.doctype.website_item.website_item import make_website_item


def execute():
	"""
	Convert all Item links to Website Item link values in
	exisitng 'Item Card Group' Web Page Block data.
	"""
	frappe.reload_doc("webshop", "web_template", "item_card_group")

	blocks = frappe.db.get_all(
		"Web Page Block",
		filters={"web_template": "Item Card Group"},
		fields=["parent", "web_template_values", "name"],
	)

	fields = generate_fields_to_edit()

	for block in blocks:
		web_template_value = json.loads(block.get("web_template_values"))

		for field in fields:
			item = web_template_value.get(field)
			if not item:
				continue

			if frappe.db.exists("Website Item", {"item_code": item}):
				website_item = frappe.db.get_value("Website Item", {"item_code": item})
			else:
				website_item = make_new_website_item(item)

			if website_item:
				web_template_value[field] = website_item

		frappe.db.set_value(
			"Web Page Block", block.name, "web_template_values", json.dumps(web_template_value)
		)


def generate_fields_to_edit() -> List:
	fields = []
	for i in range(1, 13):
		fields.append(f"card_{i}_item")  # fields like 'card_1_item', etc.

	return fields


def make_new_website_item(item: str) -> Union[str, None]:
	try:
		doc = frappe.get_doc("Item", item)
		web_item = make_website_item(doc)  # returns [website_item.name, item_name]
		return web_item[0]
	except Exception:
		doc.log_error("Website Item creation failed")
		return None