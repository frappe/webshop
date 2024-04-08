import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
	frappe.reload_doc("setup", "doctype", "item_group")

	make_property_setter("Item Group", "", "has_web_view", 1, "Check", for_doctype=True, validate_fields_for_doctype=False)
	make_property_setter("Item Group", "", "allow_guest_to_view", 1, "Check", for_doctype=True, validate_fields_for_doctype=False)
