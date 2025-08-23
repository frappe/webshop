details = frappe.call("webshop.webshop.shopping_cart.cart.get_cart_quotation")
# data.details = details
data.addresses = details["shipping_addresses"]
data.selected_address = details["doc"].shipping_address_name

data.page_data = {
    "url": frappe.get_url(),
    "selected": details["doc"].shipping_address_name
}