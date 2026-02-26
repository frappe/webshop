import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""Add UPI payment tracking fields to Sales Order."""
	custom_fields = {
		"Sales Order": [
			{
				"fieldname": "upi_payment_section",
				"fieldtype": "Section Break",
				"label": "UPI Payment Details",
				"insert_after": "payment_schedule",
				"collapsible": 1,
			},
			{
				"fieldname": "upi_transaction_id",
				"fieldtype": "Data",
				"label": "UPI Transaction ID",
				"insert_after": "upi_payment_section",
				"read_only": 1,
			},
			{
				"fieldname": "upi_payment_date",
				"fieldtype": "Datetime",
				"label": "UPI Payment Date",
				"insert_after": "upi_transaction_id",
				"read_only": 1,
			},
			{
				"fieldname": "column_break_upi",
				"fieldtype": "Column Break",
				"insert_after": "upi_payment_date",
			},
			{
				"fieldname": "upi_payment_status",
				"fieldtype": "Select",
				"label": "UPI Payment Status",
				"options": "\nPending\nPaid",
				"insert_after": "column_break_upi",
				"read_only": 1,
				"in_list_view": 1,
			},
		]
	}

	create_custom_fields(custom_fields)
