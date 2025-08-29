data.should_redirect = frappe.call("webshop.webshop.shopping_cart.cart.should_redirect_on_cart")

details = frappe.call("webshop.webshop.shopping_cart.cart.get_cart_quotation")
data.all_details = details
print(details["doc"].as_dict(),"detailsssss")
doc = details["doc"].as_dict()
prices = details["prices"]

for item in doc["items"]:
    item_code = item["item_code"]
    if item_code in prices:
        price_info = prices[item_code]
        # Strip currency symbols and commas, then convert to float
        item["rate"] = price_info["rate"]
        item["amount"] = price_info["amount"]
# data.details = details
data.quotation = doc["items"]
data.prices = prices
data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = False
data.page_data = {
    "url": frappe.get_url()
    # "name": details["web_item_name"],
    # "code": details["item_code"],
    # "has_variant": details["has_variants"],
}