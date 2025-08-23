orders = frappe.call("webshop.webshop.api.get_all_orders")
print(orders)

for order in orders:
    order["link"] = f"/order-new/{order['name']}"

data.orders = orders

data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"