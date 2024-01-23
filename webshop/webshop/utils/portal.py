import frappe
from frappe.utils.nestedset import get_root_of

from erpnext.portal.utils import create_customer_or_supplier

from webshop.webshop.doctype.webshop_settings.webshop_settings import (
    get_shopping_cart_settings,
)
from webshop.webshop.shopping_cart.cart import get_debtors_account


def update_debtors_account():
	doc_type = debtors_account = None
	user = frappe.session.user

	if frappe.db.get_value("User", user, "user_type") != "Website User":
		return

	user_roles = frappe.get_roles()
	portal_settings = frappe.get_single("Portal Settings")
	default_role = portal_settings.default_role

	if default_role not in ["Customer", "Supplier"]:
		return

	if portal_settings.default_role and portal_settings.default_role in user_roles:
		doc_type = portal_settings.default_role

	if not doc_type:
		return

	if doc_type != "Customer":
		return

	if frappe.db.exists(doc_type, user):
		party = frappe.get_doc(doc_type, user)
	else:
		party = create_customer_or_supplier()

	if not party:
		return

	fullname = frappe.utils.get_fullname(user)
	cart_settings = get_shopping_cart_settings()

	party.update(
		{
			"customer_name": fullname,
			"customer_type": "Individual",
			"customer_group": cart_settings.default_customer_group,
			"territory": get_root_of("Territory"),
		}
	)

	if cart_settings.enable_checkout:
		debtors_account = get_debtors_account(cart_settings)

	if not debtors_account:
		return party

	party.update(
		{"accounts": [{"company": cart_settings.company, "account": debtors_account}]}
	)

	return party
