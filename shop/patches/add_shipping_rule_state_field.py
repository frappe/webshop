import frappe
from shop.setup.install import add_custom_fields

def execute():
	frappe.reload_doc("shop", "doctype", "shipping_rule_state")
	add_custom_fields()
