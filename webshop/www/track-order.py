import frappe
from frappe import _

def get_context(context):
	context.no_cache = 1
	context.order_id = frappe.form_dict.get("id")
	context.title = _("Track Order")
	context.body_class = "track-order-page"
