import frappe
from frappe import _
from frappe.utils import add_to_date, cint, get_url, now_datetime


def get_abandoned_cart_candidates(hours=24, limit=50):
	cutoff = add_to_date(now_datetime(), hours=-(cint(hours) or 24))
	return frappe.get_all(
		"Quotation",
		filters={
			"order_type": "Shopping Cart",
			"docstatus": 0,
			"total_qty": [">", 0],
			"contact_email": ["is", "set"],
			"modified": ["<=", cutoff],
			"abandoned_cart_reminder_sent": ["!=", 1],
		},
		fields=[
			"name",
			"customer_name",
			"contact_email",
			"grand_total",
			"currency",
			"total_qty",
			"modified",
		],
		order_by="modified asc",
		limit=cint(limit) or 50,
	)


def send_abandoned_cart_reminders(hours=24, limit=50):
	candidates = get_abandoned_cart_candidates(hours=hours, limit=limit)
	for cart in candidates:
		try:
			send_abandoned_cart_reminder(cart)
		except Exception:
			frappe.log_error(frappe.get_traceback(), _("Abandoned Cart Reminder Failed"))

	return len(candidates)


def send_abandoned_cart_reminder(cart):
	cart_url = get_url("/cart")
	subject = _("Your Euro Plast cart is waiting")
	message = frappe.render_template(
		"""
		<p>{{ _("Hi") }} {{ customer_name or "" }},</p>
		<p>{{ _("You left") }} {{ total_qty|int }} {{ _("item(s) in your cart.") }}</p>
		<p>{{ _("Cart total") }}: <strong>{{ currency }} {{ grand_total }}</strong></p>
		<p><a href="{{ cart_url }}">{{ _("Continue checkout") }}</a></p>
		<p>{{ _("If you already placed your order, you can ignore this message.") }}</p>
		""",
		{
			"customer_name": cart.customer_name,
			"total_qty": cart.total_qty,
			"currency": cart.currency,
			"grand_total": cart.grand_total,
			"cart_url": cart_url,
		},
	)

	frappe.sendmail(
		recipients=[cart.contact_email],
		subject=subject,
		message=message,
		now=False,
	)

	frappe.db.set_value(
		"Quotation",
		cart.name,
		{
			"abandoned_cart_reminder_sent": 1,
			"abandoned_cart_last_reminder_on": now_datetime(),
			"abandoned_cart_reminder_count": 1,
		},
		update_modified=False,
	)
	frappe.get_doc("Quotation", cart.name).add_comment("Comment", _("Abandoned cart reminder queued."))
