import frappe
from webshop.webshop.utils.customer_service import get_or_create_customer_for_user


def update_debtors_account():
	"""
	Legacy function that now delegates to centralized customer service.
	Maintained for backward compatibility with existing hooks.
	"""
	user = frappe.session.user

	# Quick checks for early exit (same as before)
	if frappe.db.get_value("User", user, "user_type") != "Website User":
		return

	portal_settings = frappe.get_single("Portal Settings")
	if portal_settings.default_role != "Customer":
		return

	user_roles = frappe.get_roles()
	if portal_settings.default_role not in user_roles:
		return

	# Delegate to centralized service
	customer = get_or_create_customer_for_user(user=user)
	return customer
