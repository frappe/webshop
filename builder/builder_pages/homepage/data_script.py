homepage_details = frappe.call("webshop.webshop.api.get_webshop_homepage_content")
data.hero_image = homepage_details["hero_image"]
data.collections = homepage_details["collections"]

data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"