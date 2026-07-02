import frappe
from frappe import _


def can_view_sales_order(order_id):
	order = frappe.db.get_value(
		"Sales Order",
		order_id,
		["name", "contact_email", "customer"],
		as_dict=True,
	)
	if not order:
		return False

	if frappe.session.user == "Guest":
		return frappe.cache().get_value(f"checkout_sales_order_{frappe.session.id}") == order.name

	if order.contact_email and order.contact_email == frappe.session.user:
		return True

	linked_customers = frappe.get_all(
		"Portal User",
		filters={"user": frappe.session.user, "parenttype": "Customer"},
		pluck="parent",
	)
	return bool(order.customer and order.customer in linked_customers)


def get_context(context):
	context.no_cache = 1
	order_id = frappe.form_dict.get("id")
	context.order_id = order_id
	context.title = _("Order Successful")
	context.not_allowed = False
	context.doc = None
	context.cart_settings = frappe.get_cached_doc("Webshop Settings")
	context.account_ready = False
	context.account_created = False
	context.account_email = None
	
	if not order_id:
		frappe.local.flags.redirect_location = "/all-products"
		raise frappe.Redirect

	try:
		if not can_view_sales_order(order_id):
			context.not_allowed = True
			return

		context.doc = frappe.get_doc("Sales Order", order_id)
		context.doc.check_permission = lambda *args, **kwargs: True
		context.account_ready = frappe.form_dict.get("account") == "1"
		context.account_created = frappe.form_dict.get("account_created") == "1"
		context.account_email = frappe.form_dict.get("account_email") or context.doc.get("contact_email")
	except frappe.DoesNotExistError:
		frappe.local.flags.redirect_location = "/all-products"
		raise frappe.Redirect
