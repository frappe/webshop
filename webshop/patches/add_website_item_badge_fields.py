import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Website Item": [
				{
					"fieldname": "badge_section",
					"label": "Product Badge",
					"fieldtype": "Section Break",
					"insert_after": "slideshow",
					"collapsible": 1,
				},
				{
					"fieldname": "badge_label",
					"label": "Badge Label",
					"fieldtype": "Data",
					"insert_after": "badge_section",
					"description": "Example: New Arrival, Bestseller, Food Grade, Sale",
				},
				{
					"fieldname": "badge_color",
					"label": "Badge Color",
					"fieldtype": "Color",
					"insert_after": "badge_label",
					"default": "#B0008E",
				},
				{
					"fieldname": "badge_priority",
					"label": "Badge Priority",
					"fieldtype": "Int",
					"insert_after": "badge_color",
					"description": "Higher priority badges can be used for sorting or future campaigns.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Website Item")
