# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import cint

from webshop.webshop.doctype.webshop_settings.webshop_settings import get_shopping_cart_settings
from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website
from webshop.webshop.shopping_cart.cart import get_party

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
def get_product_filter_data_for_item_groups(item_groups=None, item_groups_mapping=None, page=0):
	"""
	Returns filtered products for specific Item Groups.

	Args:
		item_groups (list): List of valid Item Group names
		item_groups_mapping (dict): Mapping of item groups to their respective filters
	Returns:
		list: List of Website Items that belong to all specified item groups
	"""
	page = cint(page) if page else 0
	engine = ProductQuery()
	page_length = engine.settings.products_per_page or 20
	if not item_groups:
		return get_product_filter_data(query_args={"start": (page - 1) * page_length})

	select_clause = ','.join([f"wi.{field}" for field in engine.fields])
	group_clause = ','.join([frappe.db.escape(item) for item in item_groups])
	having_clause = " and ".join([f"SUM(wig.item_group IN ({','.join([frappe.db.escape(item) for item in item_groups])})) > 0" for key, item_groups in item_groups_mapping.items()])
	query = f"""
		SELECT {select_clause}
		FROM `tabWebsite Item` wi
		INNER JOIN `tabWebsite Item Group` wig ON wi.name = wig.parent
		WHERE wig.parentfield = 'custom_website_item_groups_multiselect'
		AND wig.item_group IN ({group_clause})
		GROUP BY wi.name
		HAVING {having_clause}
		ORDER BY wi.ranking DESC
		LIMIT {page_length + 1} OFFSET {(page - 1) * page_length}
	"""
 
	result = frappe.db.sql(query, as_dict=1)
 	# sort combined results by ranking
	result = sorted(result, key=lambda x: x.get("ranking"), reverse=True)
	if engine.settings.enabled:
		cart_items = engine.get_cart_items()

		result, discount_list = engine.add_display_details(result, [], cart_items)
	print("result", result, len(result), page_length)
	return {
		"items": result[:page_length] or [],
		"filters": {},
		"settings": engine.settings,
		"sub_categories": [],
		"items_count": frappe.db.count("Website Item"),
		"has_more_items": len(result) > page_length,
	}

@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")

@frappe.whitelist(allow_guest=True)
def get_item_group_details(item_group):
	"""
	Returns details of the given Item Group.
	"""
	all_filters = ProductFiltersBuilder().get_field_filters()
	all_item_groups_allowed_in_website = []
	if not all_filters:
		frappe.throw(
			("No filters are defined for the website. Please define filters in Webshop Settings."),
			frappe.DoesNotExistError,
		)
	for filter in all_filters:
		all_item_groups_allowed_in_website.extend(filter[1])
	# print("all_item_groups_allowed_in_website", all_item_groups_allowed_in_website, item_group)
	if item_group not in all_item_groups_allowed_in_website:
		frappe.throw(
			("Item Group {0} is not allowed in the website.").format(item_group),
			frappe.DoesNotExistError,
		)
	item_group_doc = frappe.get_doc("Item Group", item_group)
	return {
		"item_group_name": item_group_doc.item_group_name,
		"description": item_group_doc.description,
		"image": item_group_doc.image,
	}

@frappe.whitelist(allow_guest=True)
def get_webshop_homepage_content():
	"""
	Returns the content of the Webshop Homepage.
	"""
	content = frappe.get_doc("Webshop Homepage")
	hero_image = content.hero_image
	collections = content.homepage_collections
	additional_details = content.additional_details
	details_for_collections = []
	for collection in collections:
		details = get_item_group_details(collection.item_group)
		details_for_collections.append({
			"item_group": collection.item_group,
			"description": details["description"],
			"image": details["image"],
			"url": f"/collections/{collection.item_group}",
		})
	# print({
	# 	"hero_image": hero_image,
	# 	"collections": details_for_collections,
	# 	"additional_details": additional_details,
	# })
	return {
		"hero_image": hero_image,
		"collections": details_for_collections,
		"additional_details": additional_details,
	}


@frappe.whitelist()
def get_all_quotations(party=None):
    if not party:
        party = get_party()
    quotations = frappe.get_all(
		"Quotation",
		fields=["name", "total_qty", "transaction_date", "grand_total", "status"],
		filters={
			"party_name": party.name,
			"contact_email": frappe.session.user,
			"order_type": "Shopping Cart",
			"docstatus": 1,
		},
		order_by="modified desc",
	)
    # all_quotes = []
    # for quotation in quotations:
    #     print("price: ", quotation.get_formatted("grand_total"))
    return quotations

@frappe.whitelist()
def get_quotation_info(name, party=None):
	if not party:
		party = get_party()
	qdoc =  frappe.get_doc("Quotation", name)
	if not qdoc:
		frappe.throw("Quotation not found", frappe.DoesNotExistError)
	if qdoc.party_name != party.name:
		frappe.throw("Quotation does not belong to this party", frappe.PermissionError)
	if qdoc.contact_email != frappe.session.user:
		frappe.throw("Quotation does not belong to this user", frappe.PermissionError)
	# print(qdoc.get("items",[]))
	return qdoc


@frappe.whitelist()
def get_all_orders(party=None):
    if not party:
        party = get_party()
    orders = frappe.get_all(
		"Sales Order",
		fields=["name", "total_qty", "transaction_date", "grand_total", "status"],
		filters={
			"customer": party.name,
			"contact_email": frappe.session.user,
			"order_type": "Shopping Cart",
			"docstatus": 1,
		},
		order_by="modified desc",
	)
    return orders

@frappe.whitelist()
def get_order_info(name, party=None):
	if not party:
		party = get_party()
	qdoc =  frappe.get_doc("Sales Order", name)
	if not qdoc:
		frappe.throw("Order not found", frappe.DoesNotExistError)
	if qdoc.customer_name != party.name:
		frappe.throw("Order does not belong to this party", frappe.PermissionError)
	if qdoc.contact_email != frappe.session.user:
		frappe.throw("Order does not belong to this user", frappe.PermissionError)
	# print(qdoc.get("items",[]))
	return {"doc": qdoc, "cart_settings": frappe.get_cached_doc("Webshop Settings")}

@frappe.whitelist(allow_guest=True)
def get_wishlist_items():
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
    if not frappe.db.exists("Wishlist", frappe.session.user):
        return []
    return frappe.db.get_all(
		"Wishlist Item",
		filters={"parent": frappe.session.user},
		fields=[
			"web_item_name",
			"item_code",
			"item_name",
			"website_item",
			"warehouse",
			"image",
			"item_group",
			"route",
		],
	)