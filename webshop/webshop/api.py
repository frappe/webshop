# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import cint, flt

from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website


# @frappe.whitelist(allow_guest=True)
# def get_product_filter_data(query_args=None):
# 	"""
# 	Returns filtered products and discount filters.

# 	Args:
# 		query_args (dict): contains filters to get products list

# 	Query Args filters:
# 		search (str): Search Term.
# 		field_filters (dict): Keys include item_group, brand, etc.
# 		attribute_filters(dict): Keys include Color, Size, etc.
# 		start (int): Offset items by
# 		item_group (str): Valid Item Group
# 		from_filters (bool): Set as True to jump to page 1
# 	"""
# 	if isinstance(query_args, str):
# 		query_args = json.loads(query_args)

# 	query_args = frappe._dict(query_args or {})

# 	if query_args:
# 		search = query_args.get("search")
# 		field_filters = query_args.get("field_filters", {})
# 		attribute_filters = query_args.get("attribute_filters", {})
# 		start = cint(query_args.start) if query_args.get("start") else 0
# 		item_group = query_args.get("item_group")
# 		from_filters = query_args.get("from_filters")
# 	else:
# 		search, attribute_filters, item_group, from_filters = None, None, None, None
# 		field_filters = {}
# 		start = 0

# 	# if new filter is checked, reset start to show filtered items from page 1
# 	if from_filters:
# 		start = 0

# 	sub_categories = []
# 	if item_group:
# 		sub_categories = get_child_groups_for_website(item_group, immediate=True)

# 	engine = ProductQuery()

# 	try:
# 		result = engine.query(
# 			attribute_filters,
# 			field_filters,
# 			search_term=search,
# 			start=start,
# 			item_group=item_group,
# 		)
# 	except Exception:
# 		frappe.log_error("Product query with filter failed")
# 		return {"exc": "Something went wrong!"}

# 	# discount filter data
# 	filters = {}
# 	discounts = result["discounts"]

# 	if discounts:
# 		filter_engine = ProductFiltersBuilder()
# 		filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

# 	return {
# 		"items": result["items"] or [],
# 		"filters": filters,
# 		"settings": engine.settings,
# 		"sub_categories": sub_categories,
# 		"items_count": result["items_count"],
# 	}

# ###############################################################################################

# @frappe.whitelist(allow_guest=True)
# def get_product_filter_data(query_args=None):
# 	"""
# 	Returns filtered products and discount filters.

# 	Args:
# 		query_args (dict): contains filters to get products list

# 	Query Args filters:
# 		search (str): Search Term.
# 		field_filters (dict): Keys include item_group, brand, etc.
# 		attribute_filters(dict): Keys include Color, Size, etc.
# 		start (int): Offset items by
# 		item_group (str): Valid Item Group
# 		from_filters (bool): Set as True to jump to page 1
# 	"""
# 	if isinstance(query_args, str):
# 		query_args = json.loads(query_args)

# 	query_args = frappe._dict(query_args or {})

# 	if query_args:
# 		search = query_args.get("search")
# 		field_filters = query_args.get("field_filters", {})
# 		attribute_filters = query_args.get("attribute_filters", {})
# 		start = cint(query_args.start) if query_args.get("start") else 0
# 		item_group = query_args.get("item_group")
# 		from_filters = query_args.get("from_filters")
# 	else:
# 		search, attribute_filters, item_group, from_filters = None, None, None, None
# 		field_filters = {}
# 		start = 0

# 	# if new filter is checked, reset start to show filtered items from page 1
# 	if from_filters:
# 		start = 0

# 	sub_categories = []
# 	if item_group:
# 		sub_categories = get_child_groups_for_website(item_group, immediate=True)

# 	engine = ProductQuery()

# 	try:
# 		result = engine.query(
# 			attribute_filters,
# 			field_filters,
# 			search_term=search,
# 			start=start,
# 			item_group=item_group,
# 		)
# 	except Exception:
# 		frappe.log_error("Product query with filter failed")
# 		return {"exc": "Something went wrong!"}

# 	# discount filter data
# 	filters = {}
# 	discounts = result["discounts"]

# 	if discounts:
# 		filter_engine = ProductFiltersBuilder()
# 		filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

# 	for item in result["items"]:
# 		item_code = item.get("item_code")
# 		website_warehouse = item.get("website_warehouse")

# 		if not website_warehouse:
# 			website_warehouse = frappe.db.get_value("Website Item", item.get("name"), "website_warehouse")

# 		actual_qty = 0
# 		if item_code and website_warehouse:
# 			actual_qty = frappe.db.get_value("Bin", {
# 				"item_code": item_code,
# 				"warehouse": website_warehouse
# 			}, "actual_qty") or 0

# 		item["actual_qty"] = flt(actual_qty)
# 		item["stock_qty"] = flt(actual_qty)
# 		item["in_stock"] = actual_qty > 0


# 	return {
# 		"items": result["items"] or [],
# 		"filters": filters,
# 		"settings": engine.settings,
# 		"sub_categories": sub_categories,
# 		"items_count": result["items_count"],
# 	}

# ###############################################################################################

# @frappe.whitelist()
# def get_product_filter_data(start=0, search=None, item_group=None, fields=None, attributes=None):
# 	if isinstance(fields, str):
# 		fields = json.loads(fields)
# 	if isinstance(attributes, str):
# 		attributes = json.loads(attributes)

# 	from webshop.webshop.product_data_engine.query import ProductQuery

# 	# استخدم Webshop Settings لتحديد الترتيب
# 	settings = frappe.get_cached_doc("Webshop Settings")
# 	# sort_by = settings.sort_by or "ranking_desc"
# 	sort_by = settings.sort_by or "most_used"


# 	query_engine = ProductQuery()
# 	query_engine.set_sort_order(sort_by)

# 	frappe.log_error("Using sort order: " + query_engine.sort_order)

# 	return query_engine.query(
# 		attributes=attributes,
# 		fields=fields,
# 		search_term=search,
# 		start=start,
# 		item_group=item_group,
# 	)

# ###############################################################################################

@frappe.whitelist(allow_guest=True)
def get_product_filter_data(query_args=None):
	if isinstance(query_args, str):
		query_args = json.loads(query_args)

	query_args = frappe._dict(query_args or {})

	search = query_args.get("search")
	field_filters = query_args.get("field_filters", {})
	attribute_filters = query_args.get("attribute_filters", {})
	start = cint(query_args.get("start") or 0)
	item_group = query_args.get("item_group")
	from_filters = query_args.get("from_filters")

	if from_filters:
		start = 0

	settings = frappe.get_cached_doc("Webshop Settings")
	sort_by = settings.sort_by or "most_used"

	engine = ProductQuery()
	engine.set_sort_order(sort_by)

	frappe.log_error("Using sort order: " + engine.sort_order)

	try:
		result = engine.query(
			attribute_filters,
			field_filters,
			search_term=search,
			start=start,
			item_group=item_group,
		)
	except Exception as e:
		frappe.log_error(f"Product query failed: {frappe.get_traceback()}")
		return {"exc": "Something went wrong!"}

	filters = {}
	discounts = result["discounts"]

	if discounts:
		filter_engine = ProductFiltersBuilder()
		filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

	for item in result["items"]:
		item_code = item.get("item_code")
		website_warehouse = item.get("website_warehouse") or frappe.db.get_value(
			"Website Item", item.get("name"), "website_warehouse"
		)

		actual_qty = 0
		if item_code and website_warehouse:
			actual_qty = frappe.db.get_value(
				"Bin",
				{"item_code": item_code, "warehouse": website_warehouse},
				"actual_qty"
			) or 0

		item["actual_qty"] = flt(actual_qty)
		item["stock_qty"] = flt(actual_qty)
		item["in_stock"] = actual_qty > 0

	sub_categories = []
	if item_group:
		sub_categories = get_child_groups_for_website(item_group, immediate=True)

	return {
		"items": result["items"] or [],
		"filters": filters,
		"settings": engine.settings,
		"sub_categories": sub_categories,
		"items_count": result["items_count"],
	}


@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")