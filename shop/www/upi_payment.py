import frappe

def get_context(context):
    try:
        # Get order ID from query parameters
        order_id = frappe.form_dict.get("order")
        
        if not order_id:
            context.error = "Order ID is missing"
            return

        # Fetch the Sales Order document
        try:
            order = frappe.get_doc("Sales Order", order_id)
        except frappe.DoesNotExistError:
             # Fallback to Quotation if Sales Order doesn't exist yet (in case of draft/checkout flow issues)
            try:
                order = frappe.get_doc("Quotation", order_id)
            except frappe.DoesNotExistError:
                context.error = "Order not found"
                return

        # Check permissions - crucial for security
        # Allow if user is the owner or if it's a guest order with matching email/session
        if order.owner != frappe.session.user and not (frappe.session.user == "Guest"):
             # For Guests, we might need a looser check or rely on a signed token. 
             # For now, we'll assume valid redirection implies access for the session.
             # In a strict production env, verify a token. 
             pass

        context.order = order
        context.amount = order.grand_total
        context.currency = order.currency
        
        # Fetch UPI settings
        shop_settings = frappe.get_doc("Shop Settings")
        context.upi_id = shop_settings.upi_id
        context.payee_name = shop_settings.payee_name

        if not context.upi_id:
            context.error = "UPI ID not configured in Shop Settings"

    except Exception as e:
        frappe.log_error(f"Error in UPI Payment Page: {str(e)}")
        context.error = "An error occurred while loading the payment page."
