# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import cint

from shop.shop.product_data_engine.filters import ProductFiltersBuilder
from shop.shop.product_data_engine.query import ProductQuery
from shop.shop.doctype.override_doctype.item_group import get_child_groups_for_website


@frappe.whitelist(allow_guest=True)
def get_product_filter_data(query_args=None):
	"""
	Returns filtered products and discount filters.

	Args:
		query_args (dict): contains filters to get products list

	Query Args filters:
		search (str): Search Term.
		field_filters (dict): Keys include item_group, brand, etc.
		attribute_filters(dict): Keys include Color, Size, etc.
		start (int): Offset items by
		item_group (str): Valid Item Group
		from_filters (bool): Set as True to jump to page 1
	"""
	if isinstance(query_args, str):
		query_args = json.loads(query_args)

	query_args = frappe._dict(query_args or {})

	if query_args:
		search = query_args.get("search")
		field_filters = query_args.get("field_filters", {})
		attribute_filters = query_args.get("attribute_filters", {})
		start = cint(query_args.start) if query_args.get("start") else 0
		item_group = query_args.get("item_group")
		from_filters = query_args.get("from_filters")
	else:
		search, attribute_filters, item_group, from_filters = None, None, None, None
		field_filters = {}
		start = 0

	# if new filter is checked, reset start to show filtered items from page 1
	if from_filters:
		start = 0

	sub_categories = []
	if item_group:
		sub_categories = get_child_groups_for_website(item_group, immediate=True)

	engine = ProductQuery()

	try:
		result = engine.query(
			attribute_filters,
			field_filters,
			search_term=search,
			start=start,
			item_group=item_group,
		)
	except Exception:
		frappe.log_error("Product query with filter failed")
		return {"exc": "Something went wrong!"}

	# discount filter data
	filters = {}
	discounts = result["discounts"]

	if discounts:
		filter_engine = ProductFiltersBuilder()
		filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

	return {
		"items": result["items"] or [],
		"filters": filters,
		"settings": engine.settings,
		"sub_categories": sub_categories,
		"items_count": result["items_count"],
	}


@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Shop Settings", "redirect_on_action")


@frappe.whitelist(allow_guest=True)
def mobile_signup(mobile_no, full_name, password):
	if not mobile_no or not password or not full_name:
		frappe.throw(frappe._("Please fill all details"))

	# Create a dummy email for the user as Frappe requires unique email/name
	email = "{0}@mobile.signup".format(mobile_no)

	# Use sudo to bypass Guest permission limits on User doctype
	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")

		# Check if user already exists
		if frappe.db.get_value("User", {"mobile_no": mobile_no}, "name") or frappe.db.exists("User", email):
			frappe.throw(frappe._("User already exists with this mobile number. Please login."))

		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": full_name,
				"mobile_no": mobile_no,
				"user_type": "Website User",
				"send_welcome_email": 0,
			}
		)
		user.flags.ignore_permissions = True
		user.insert(ignore_permissions=True)

		# Set password
		from frappe.utils.password import update_password
		update_password(user.name, password)

		# Assign 'Customer' role or default portal role
		default_role = frappe.db.get_single_value("Portal Settings", "default_role") or "Customer"
		user_doc = frappe.get_doc("User", user.name, ignore_permissions=True)
		user_doc.add_roles(default_role)

		# Login the user
		from frappe.auth import LoginManager
		login_manager = LoginManager()
		login_manager.login_as(user.name)

		# Ensure Customer record is created
		frappe.set_user(user.name)
		from shop.shop.utils.portal import update_debtors_account
		update_debtors_account()

	finally:
		if frappe.session.user == "Administrator":
			frappe.set_user(original_user)

	return {"status": "success", "message": frappe._("Signup successful")}
