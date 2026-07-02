import frappe
from frappe import _
from webshop.webshop.shopping_cart.cart import get_cart_quotation

no_cache = 1

def get_empty_checkout_doc():
	doc = frappe.new_doc("Quotation")
	doc.items = []
	doc.taxes = []
	doc.grand_total = 0
	doc.rounded_total = 0
	return doc

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = False
	context.body_class = "checkout-page"
	context.title = _("Checkout")
	
	# Always provide cart_settings to avoid 500 errors in Jinja on first access
	context.cart_settings = frappe.get_doc("Webshop Settings")
	
	try:
		context.update(get_cart_quotation(for_checkout=True))
	except frappe.Redirect:
		context.checkout_error = _("Please sign in to continue checkout.")
		if not context.get("doc"):
			context.doc = get_empty_checkout_doc()
		context.shipping_addresses = []
		context.billing_addresses = []
		context.shipping_rules = []
		context.available_shipping_methods = []
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), _("Checkout Context Error"))
		context.checkout_error = _(
			"Checkout is temporarily unavailable. Please refresh the page or contact support."
		)
		# Still provide a minimal context to prevent template crashes while showing the error.
		if not context.get("doc"):
			context.doc = get_empty_checkout_doc()
		context.shipping_addresses = []
		context.billing_addresses = []
		context.shipping_rules = []
		context.available_shipping_methods = []
