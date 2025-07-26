current_user = frappe.session.user
url = frappe.get_url();
data.page_data = {
    "url": url,
}
items = frappe.call("webshop.webshop.api.get_wishlist_items")
for item in items:
    item.route = f"/item/{item['website_item']}"
    
data.items = items

data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"


data.page_data = {
    "url": frappe.get_url()
}