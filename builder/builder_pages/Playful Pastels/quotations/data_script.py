quotes = frappe.call("webshop.webshop.api.get_all_quotations")
print(quotes)

for quote in quotes:
    quote["link"] = f"/quotation-new/{quote['name']}"

data.quotes = quotes
data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"