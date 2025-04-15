import frappe
from frappe.website.utils import clear_cache

def execute():
	routes = frappe.get_all("Item Group", filters={"show_in_website": 1, "route": ("is", "set")}, pluck="route")
	for route in routes:
		clear_cache(route)