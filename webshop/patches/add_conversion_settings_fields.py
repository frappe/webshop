from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
import frappe


def get_fields():
	return {
		"Webshop Settings": [
			{
				"fieldname": "conversion_section",
				"label": "Conversion Boosters",
				"fieldtype": "Section Break",
				"insert_after": "redirect_on_action",
				"collapsible": 1,
			},
			{
				"fieldname": "delivery_promise_text",
				"label": "Delivery Promise Text",
				"fieldtype": "Data",
				"insert_after": "conversion_section",
				"default": "Delivery in 2-4 working days",
			},
			{
				"fieldname": "returns_promise_text",
				"label": "Returns / Support Promise Text",
				"fieldtype": "Data",
				"insert_after": "delivery_promise_text",
				"default": "Easy exchange and support after purchase",
			},
			{
				"fieldname": "first_order_coupon_code",
				"label": "First Order Coupon Code",
				"fieldtype": "Data",
				"insert_after": "returns_promise_text",
			},
			{
				"fieldname": "first_order_coupon_text",
				"label": "First Order Coupon Text",
				"fieldtype": "Data",
				"insert_after": "first_order_coupon_code",
				"default": "Use this code on your first order",
			},
			{
				"fieldname": "conversion_column_break",
				"fieldtype": "Column Break",
				"insert_after": "first_order_coupon_text",
			},
			{
				"fieldname": "low_stock_threshold",
				"label": "Low Stock Threshold",
				"fieldtype": "Int",
				"insert_after": "conversion_column_break",
				"default": "5",
			},
			{
				"fieldname": "enable_exit_intent_recovery",
				"label": "Enable Exit Intent Cart Recovery",
				"fieldtype": "Check",
				"insert_after": "low_stock_threshold",
				"default": "1",
			},
		]
	}


def execute():
	create_custom_fields(get_fields(), ignore_validate=True)
	if frappe.db.get_single_value("Webshop Settings", "enable_exit_intent_recovery") is None:
		frappe.db.set_single_value("Webshop Settings", "enable_exit_intent_recovery", 1)
	frappe.clear_cache(doctype="Webshop Settings")
