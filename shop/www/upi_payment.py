import frappe

# CRITICAL: Disable Frappe page caching so the order number is always fresh
no_cache = 1

def get_context(context):
    # Disable caching at context level too
    context.no_cache = 1

    try:
        # Get order ID from query parameters
        order_id = frappe.form_dict.get("order")
        
        if not order_id:
            context.error = "Order ID is missing"
            return

        # Fetch the order with ignore_permissions so any session can view their own order
        order = None
        for doctype in ["Sales Order", "Quotation"]:
            if frappe.db.exists(doctype, order_id):
                order = frappe.get_doc(doctype, order_id)
                order.flags.ignore_permissions = True
                break

        if not order:
            context.error = "Order not found: " + order_id
            return

        context.order = order
        context.amount = order.grand_total
        context.formatted_amount = order.get_formatted("grand_total")
        context.currency = order.currency
        
        # Fetch UPI settings
        context.upi_id = frappe.db.get_single_value("Shop Settings", "upi_id")
        context.payee_name = frappe.db.get_single_value("Shop Settings", "payee_name")

        # Debug log
        frappe.logger().info(
            f"UPI Payment Page: order_id={order_id}, order.name={order.name}, "
            f"grand_total={order.grand_total}, upi_id='{context.upi_id}'"
        )

        if not context.upi_id:
            context.error = "UPI ID not configured in Shop Settings"

    except Exception as e:
        frappe.log_error(f"Error in UPI Payment Page: {str(e)}")
        context.error = f"An error occurred: {str(e)}"
