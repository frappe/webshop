import frappe


def execute():
	page = frappe.db.get_value("Web Page", {"route": "products/freshmate"}, "name")
	if page:
		frappe.db.set_value("Web Page", page, "published", 0)
