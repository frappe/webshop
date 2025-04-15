import frappe
from frappe.website.utils import clear_cache

def execute():
	for d in frappe.get_all("Item Group", filters={"show_in_website": 1}, pluck="route"):
		if d.route:
			clear_cache(d.route)