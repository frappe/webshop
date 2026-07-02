import frappe
from frappe import _

from webshop.webshop.api import require_payment_reviewer


def get_context(context):
	context.no_cache = 1
	context.title = _("Payment Verification")
	context.body_class = "payment-verification-page"

	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/payment-verification"
		raise frappe.Redirect

	require_payment_reviewer()
