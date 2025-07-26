# data.filters = {
#     "Type": [{"value": "Sofa"}, {"value": "Arm Chair"}],
#     "Collection": [
#         {"value": "Scandinavian Simplicity"},
#         {"value": "Modern Luxe"},
#         {"value": "Boho Chic"},
#         {"value": "Timeless Classics"},
#     ],
#     "Category": [
#         {"value": "Three seater"},
#         {"value": "One seater"},
#         {"value": "Two seater"},
#     ],
# }
# # we need to make this reactive
# filter_types = ["category", "collection", "type"]
# filters = []
# for key, value in frappe.form_dict.items():
#     # print(key, value, 888)
#     if key in filter_types:
#         filters.extend(value.split(","))

# # print(filters, "filters 9999")

# homepage_content = frappe.call("webshop.webshop.api.get_webshop_homepage_content")
filtered_result = frappe.call(
    "webshop.webshop.api.get_product_filter_data",
    query_args={
        "field_filters": {
            "custom_website_item_groups_multiselect": ["Sofa"],
        }
    },
)
products = filtered_result["items"]
for product in products:
    item_name = product["name"]
    product["route"] = f"item/{item_name}"
data.collections = homepage_content["collections"]
data.products = products

data.page_data = frappe.form_dict

# print(frappe.form_dict.values(), data.products, 999)


data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"