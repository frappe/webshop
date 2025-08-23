details = frappe.call("webshop.webshop.shopping_cart.cart.get_cart_quotation")
# data.details = details
data.addresses = details["billing_addresses"]
data.selected_address = details["doc"].customer_address

data.page_data = {
    "url": frappe.get_url(),
    "selected": details["doc"].customer_address
}