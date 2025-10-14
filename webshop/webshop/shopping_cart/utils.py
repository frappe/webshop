# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe

from webshop.webshop.doctype.webshop_settings.webshop_settings import is_cart_enabled
from webshop.webshop.utils.store import (
	get_active_store_context,
	get_published_stores,
	is_multi_store_enabled,
)


def show_cart_count():
	if (
		is_cart_enabled()
		and frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User"
	):
		return True

	return False


def set_cart_count(login_manager):
	# since this is run only on hooks login event
	# make sure user is already a customer
	# before trying to set cart count
	user_is_customer = is_customer()
	if not user_is_customer:
		return

	if show_cart_count():
		from webshop.webshop.shopping_cart.cart import set_cart_count

		# set_cart_count will try to fetch existing cart quotation
		# or create one if non existent (and create a customer too)
		# cart count is calculated from this quotation's items
		set_cart_count()


def clear_cart_count(login_manager):
	if show_cart_count():
		frappe.local.cookie_manager.delete_cookie("cart_count")


def update_website_context(context):
	cart_enabled = is_cart_enabled()
	context["shopping_cart_enabled"] = cart_enabled
	context["multi_store_enabled"] = is_multi_store_enabled()

	if not context["multi_store_enabled"]:
		context["stores"] = []
		context["current_store"] = None
		return

	context["stores"] = [store.as_dict() for store in get_published_stores()]
	context["current_store"] = get_active_store_context()


def is_customer():
	if frappe.session.user and frappe.session.user != "Guest":
		contact_name = frappe.get_value("Contact", {"email_id": frappe.session.user})
		if contact_name:
			contact = frappe.get_doc("Contact", contact_name)
			for link in contact.links:
				if link.link_doctype == "Customer":
					return True

		return False
