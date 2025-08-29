filter_res = frappe.call("webshop.webshop.api.get_webshop_groups")
# we need to make this reactive
filter_types = [group.lower() for group in filter_res["top_groups"]]
data.filter_mapping = filter_res["child_groups_per_node"]
filters = []
filter_map = {}
for key, value in frappe.form_dict.items():
    # print(key, value, 888)
    if key in filter_types:
        filters.extend(value.split(","))
        filter_map[key] = value.split(",")

# print(filters, "filters 9999")
try:
    page = frappe.form_dict["page"]
except:
    page = 1
data.prev_page_available = int(page) - 1
homepage_content = frappe.call("webshop.webshop.api.get_webshop_homepage_content")
# filtered_result = frappe.call(
#     "webshop.webshop.api.get_product_filter_data",
#     query_args={
#         "field_filters": {
#             "custom_website_item_groups_multiselect": filters,
#         }
#     },
# )
filtered_result = frappe.call(
    "webshop.webshop.api.get_product_filter_data_for_item_groups",
    item_groups=filters,
    item_groups_mapping=filter_map,
    page=page
)
products = filtered_result["items"]

try:
    has_more_items = filtered_result["has_more_items"]
except:
    has_more_items = len(filtered_result["items"]) < filtered_result["items_count"]

for product in products:
    item_name = product["name"]
    product["route"] = f"item/{item_name}"
data.collections = homepage_content["collections"]
data.products = products
data.no_products =  len(products) < 1
data.has_more_items = has_more_items
data.page_data = frappe.form_dict

# print(frappe.form_dict.values(), data.products, 999)


data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"