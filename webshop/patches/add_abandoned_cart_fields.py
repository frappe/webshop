import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Quotation": [
				{
					"fieldname": "abandoned_cart_section",
					"label": "Abandoned Cart Recovery",
					"fieldtype": "Section Break",
					"insert_after": "contact_email",
					"collapsible": 1,
				},
				{
					"fieldname": "abandoned_cart_reminder_sent",
					"label": "Abandoned Cart Reminder Sent",
					"fieldtype": "Check",
					"insert_after": "abandoned_cart_section",
					"read_only": 1,
				},
				{
					"fieldname": "abandoned_cart_last_reminder_on",
					"label": "Last Reminder On",
					"fieldtype": "Datetime",
					"insert_after": "abandoned_cart_reminder_sent",
					"read_only": 1,
				},
				{
					"fieldname": "abandoned_cart_reminder_count",
					"label": "Reminder Count",
					"fieldtype": "Int",
					"insert_after": "abandoned_cart_last_reminder_on",
					"read_only": 1,
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Quotation")
