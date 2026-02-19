import frappe

def get_context(context):
    try:
        # Get order ID from query parameters
        order_id = frappe.form_dict.get("order")
        
        if not order_id:
            context.error = "Order ID is missing"
            return

        # Fetch the Sales Order document
        order = None
        for doctype in ["Sales Order", "Quotation"]:
            if frappe.db.exists(doctype, order_id):
                order = frappe.get_doc(doctype, order_id)
                break

        if not order:
            context.error = "Order not found"
            return

        context.order = order
        context.amount = order.grand_total
        context.currency = order.currency
        
        # Fetch UPI settings using get_single_value (more reliable for Singles)
        context.upi_id = frappe.db.get_single_value("Shop Settings", "upi_id")
        context.payee_name = frappe.db.get_single_value("Shop Settings", "payee_name")

        # Debug log to help troubleshoot
        frappe.logger().info(f"UPI Payment Page: upi_id='{context.upi_id}', payee_name='{context.payee_name}'")

        if not context.upi_id:
            context.error = "UPI ID not configured in Shop Settings"

    except Exception as e:
        frappe.log_error(f"Error in UPI Payment Page: {str(e)}")
        context.error = f"An error occurred: {str(e)}"
