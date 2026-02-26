import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Homepage"):
		return
	if not frappe.db.exists("Custom Field", {"fieldname": "products", "dt": "Homepage"}):
		custom_fields = {
			"Homepage": [
				dict(
					fieldname="products_section_break",
					label="Products",
					fieldtype="Section Break",
					insert_after="hero_section",
				),
				dict(
					fieldname="products_url",
					label="URL for All Products",
					fieldtype="Data",
					insert_after="products_section_break",
				),
				dict(
					fieldname="products",
					label="Products",
					fieldtype="Table",
					insert_after="products_url",
					options="Homepage Featured Product",
				),
			],
		}

		create_custom_fields(custom_fields)
