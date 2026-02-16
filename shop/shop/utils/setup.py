import frappe

def has_ecommerce_fields() -> bool:
	table = frappe.qb.Table("tabSingles")
	query = (
		frappe.qb.from_(table)
		.select(table.field)
		.where(table.doctype == "E Commerce Settings")
		.limit(1)
	)

	data = query.run(as_dict=True)
	return bool(data)