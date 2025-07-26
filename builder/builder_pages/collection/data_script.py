homepage_details = frappe.call("webshop.webshop.api.get_webshop_homepage_content")
id = frappe.form_dict.id
print(id, "id")

collections = homepage_details["collections"]
details = None

for collection in collections:
    if collection["item_group"] == id:
        print("Found", id, collection["item_group"])
        details = collection

print(details)
data.details = details

# data.filters = {
#     "Type": [{"value": "Sofa"}, {"value": "Arm Chair"}],
#     "Category": [
#         {"value": "Three seater"},
#         {"value": "One seater"},
#         {"value": "Two seater"},
#     ],
# }
# # we need to make this reactive
# filter_types = ["category", "type"]
filters = [id]


homepage_content = frappe.call("webshop.webshop.api.get_webshop_homepage_content")
filtered_result = frappe.call(
    "webshop.webshop.api.get_product_filter_data",
    query_args={
        "field_filters": {
            "custom_website_item_groups_multiselect": filters,
        }
    },
)

products = filtered_result["items"]

for product in products:
    item_name = product["name"]
    product["route"] = f"/item/{item_name}"

data.products = products

data.page_data = frappe.form_dict

print(frappe.form_dict.values(), data.products, 999)


data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"