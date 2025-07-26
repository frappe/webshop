quotes = frappe.call("webshop.webshop.api.get_all_quotations")
print(quotes)

for quote in quotes:
    quote["link"] = f"/quotation-new/{quote['name']}"

data.quotes = quotes
