import frappe

# Prevent Frappe page caching
no_cache = 1

def get_context(context):
    context.no_cache = 1
    # We only pass static UPI settings server-side.
    # Order details are fetched dynamically via JavaScript AJAX call
    # to completely bypass any Frappe/browser page caching.
    context.upi_id = frappe.db.get_single_value("Shop Settings", "upi_id") or ""
    context.payee_name = frappe.db.get_single_value("Shop Settings", "payee_name") or ""
