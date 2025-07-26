name = frappe.form_dict.name

quote = frappe.call("webshop.webshop.api.get_quotation_info", name=name)

data.quote = quote
