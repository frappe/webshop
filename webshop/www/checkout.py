import frappe
from frappe import _
from webshop.webshop.shopping_cart.cart import get_cart_quotation

no_cache = 1

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	context.body_class = "checkout-page"
	context.title = _("Checkout")
	
	# Always provide cart_settings to avoid 500 errors in Jinja on first access
	context.cart_settings = frappe.get_doc("Webshop Settings")
	
	try:
		context.update(get_cart_quotation(for_checkout=True))
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _("Checkout Context Error"))
		# Still provide context if failure is internal, to prevent template crash
		if not context.get("doc"):
			context.doc = frappe._dict({"items": [], "taxes": [], "grand_total": 0})
