import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter


def execute():
	frappe.reload_doc("webshop", "doctype", "website_item")
	make_property_setter(
		"Website Item",
		"",
		"allow_guest_to_view",
		1,
		"Check",
		for_doctype=True,
		validate_fields_for_doctype=False,
	)
