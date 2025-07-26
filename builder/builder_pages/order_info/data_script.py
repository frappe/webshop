name = frappe.form_dict.name

order = frappe.call("webshop.webshop.api.get_order_info", name=name)

data.order = order

data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = False
data.page_data = {
    "url": frappe.get_url(),
    "doc": {
        "name": order["doc"].name,
        "doctype" : order["doc"].doctype
    }
}