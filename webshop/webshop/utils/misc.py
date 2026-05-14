import frappe

@frappe.whitelist(allow_guest=True)
def parse_json(val: str):
    return frappe.parse_json(val)

@frappe.whitelist(allow_guest=True)
def as_json(val: dict | list):
    return  frappe.as_json(val)
