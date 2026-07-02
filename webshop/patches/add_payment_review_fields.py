import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"Sales Order": [
				{
					"fieldname": "payment_method",
					"label": "Payment Method",
					"fieldtype": "Data",
					"insert_after": "currency",
					"read_only": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "payment_review_section",
					"label": "Webshop Payment Review",
					"fieldtype": "Section Break",
					"insert_after": "payment_method",
					"collapsible": 1,
				},
				{
					"fieldname": "requires_payment_review",
					"label": "Requires Payment Review",
					"fieldtype": "Check",
					"insert_after": "payment_review_section",
					"read_only": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "payment_review_status",
					"label": "Payment Review Status",
					"fieldtype": "Select",
					"options": "\nPending Verification\nApproved\nRejected",
					"insert_after": "requires_payment_review",
					"read_only": 1,
					"in_list_view": 1,
				},
				{
					"fieldname": "payment_receipt",
					"label": "Payment Receipt",
					"fieldtype": "Attach",
					"insert_after": "payment_review_status",
					"read_only": 1,
				},
				{
					"fieldname": "payment_review_notes",
					"label": "Payment Review Notes",
					"fieldtype": "Small Text",
					"insert_after": "payment_receipt",
				},
				{
					"fieldname": "payment_review_column_break",
					"fieldtype": "Column Break",
					"insert_after": "payment_review_notes",
				},
				{
					"fieldname": "payment_reviewed_by",
					"label": "Payment Reviewed By",
					"fieldtype": "Link",
					"options": "User",
					"insert_after": "payment_review_column_break",
					"read_only": 1,
				},
				{
					"fieldname": "payment_reviewed_on",
					"label": "Payment Reviewed On",
					"fieldtype": "Datetime",
					"insert_after": "payment_reviewed_by",
					"read_only": 1,
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Sales Order")
