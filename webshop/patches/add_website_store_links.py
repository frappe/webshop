import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	custom_fields = {
		"Quotation": [
			dict(
				fieldname="website_store",
				label="Website Store",
				fieldtype="Link",
				options="Website Store",
				insert_after="order_type",
				read_only=1,
				no_copy=1,
			),
		],
		"Sales Order": [
			dict(
				fieldname="website_store",
				label="Website Store",
				fieldtype="Link",
				options="Website Store",
				insert_after="order_type",
				read_only=1,
				no_copy=1,
			),
		],
	}

	create_custom_fields(custom_fields, update=True)
