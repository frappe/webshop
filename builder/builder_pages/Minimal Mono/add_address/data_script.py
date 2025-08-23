data.countries = frappe.db.get_list("Country")

data.page_data = {
    "url": frappe.get_url()
    # "name": details["web_item_name"],
    # "code": details["item_code"],
    # "has_variant": details["has_variants"],
}