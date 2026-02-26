import frappe

def get_context(context):
	context.no_cache = 1
	if frappe.session.user != "Guest":
		frappe.local.flags.redirect_location = "/cart"
		raise frappe.Redirect
