import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	order_id = frappe.form_dict.get("id")
	context.order_id = order_id
	context.title = _("Order Successful")
	
	if not order_id:
		frappe.local.flags.redirect_location = "/all-products"
		raise frappe.Redirect

	try:
		# Use ignore_permissions so Guest can see their Sales Order summary
		frappe.flags.ignore_permissions = True
		context.doc = frappe.get_doc("Sales Order", order_id)
		frappe.flags.ignore_permissions = False
		context.doc.check_permission = lambda *args, **kwargs: True # Bypass template access checks
		context.cart_settings = frappe.get_cached_doc("Webshop Settings")
		context.account_ready = frappe.form_dict.get("account") == "1"
		context.account_created = frappe.form_dict.get("account_created") == "1"
		context.account_email = frappe.form_dict.get("account_email") or context.doc.get("contact_email")
	except frappe.DoesNotExistError:
		frappe.local.flags.redirect_location = "/all-products"
		raise frappe.Redirect
