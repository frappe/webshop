# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe.utils import cint

from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import (
	get_child_groups_for_website,
)

from webshop.webshop.doctype.webshop_settings.webshop_settings import (
	get_shopping_cart_settings,
	show_quantity_in_website,
)
from webshop.webshop.shopping_cart.cart import _set_price_list
from erpnext.utilities.product import get_price
from webshop.webshop.utils.product import (
	get_non_stock_item_status,
	get_web_item_qty_in_stock,
)
from webshop.webshop.shopping_cart.cart import get_party
from webshop.webshop.utils.query_builder import build_criterion, order_col_map, website_item
from pypika import Order

def is_empty(val):
	return val in (None, "", [], {}, ())


def merge_dicts(primary, secondary):
	result = {}

	keys = set(primary.keys()) | set(secondary.keys())

	for key in keys:
		v1 = primary.get(key)
		v2 = secondary.get(key)

		# Both are dicts → recurse
		if isinstance(v1, dict) and isinstance(v2, dict):
			result[key] = merge_dicts(v1, v2)

		# Prefer non-empty
		elif is_empty(v1) and not is_empty(v2):
			result[key] = v2
		elif not is_empty(v1) and is_empty(v2):
			result[key] = v1

		# Both non-empty → priority to primary
		else:
			result[key] = v1 if not is_empty(v1) else v2

	return result


@frappe.whitelist(allow_guest=True)
def has_permission_for_webshop(
	doctype: str = "Website Item", doc: Document | None = None
):
	if frappe.session.user == "Administrator":
		return True

	if not frappe.db.get_single_value(
		"Webshop Settings", "login_required_to_view_products"
	):
		return True

	if frappe.has_permission(doctype, doc=doc):
		return True

	return False


@frappe.whitelist(allow_guest=True)
def get_product_filter_data(query_args=None):
	"""
	# Depricated in favor of list_items
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
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")


@frappe.whitelist(allow_guest=True)
def list_items(
	filters: dict | None = None,
	limit: int = 20,
	offset: int = 0,
	order: dict | None = None,  # e.g. {"created_at": "desc"} or {"ranking": "asc"}
) -> str:

	if not has_permission_for_webshop():
		frappe.throw_permission_error()

	q = (
		frappe.qb.from_(website_item)
		.select(website_item.star)
		.limit(limit)
		.offset(offset)
	)

	if filters:
		criterion = build_criterion(filters)
		if criterion is not None:
			q = q.where(criterion)

	if order:
		for field_name, direction in order.items():
			col = order_col_map.get(field_name, website_item.field(field_name))
			q = q.orderby(col, order=Order.desc if direction == "desc" else Order.asc)
	else:
		# default: ranking desc, then newest first
		q = q.orderby(website_item.ranking, order=Order.desc)
		q = q.orderby(website_item.creation, order=Order.desc)

	return q.run(as_dict=True)


@frappe.whitelist(allow_guest=True)
def get_item(item_code: str, combine_template: bool = False):
	"""
	Get item info with price / stock info
	"""

	if not has_permission_for_webshop():
		frappe.throw_permission_error()

	cart_settings = get_shopping_cart_settings()
	if not cart_settings.enabled:
		return frappe._dict({"product_info": {}})

	web_item_info = frappe.get_cached_doc("Website Item", item_code)
	if combine_template:
		if web_item_info.variant_of:
			web_template = frappe.db.get_all(
				"Website Item", filters={"item_code": web_item_info.variant_of}, limit=1
			)
			if len(web_template):
				web_template_info = frappe.get_doc("Website Item", web_template[0].name)
				combined_web_item_info = merge_dicts(
					web_item_info.as_dict(), web_template_info.as_dict()
				)
		else:
			combined_web_item_info = web_item_info

	selling_price_list = _set_price_list(cart_settings, None)

	price = {}
	if cart_settings.show_price:
		is_guest = frappe.session.user == "Guest"
		party = get_party()

		# Show Price if logged in.
		# If not logged in, check if price is hidden for guest.
		if not is_guest or not cart_settings.hide_price_for_guest:
			price = get_price(
				web_item_info.item_code,
				selling_price_list,
				cart_settings.default_customer_group,
				cart_settings.company,
				party=party,
			)

	stock_status = None

	if cart_settings.show_stock_availability:
		on_backorder = web_item_info.on_backorder
		if on_backorder:
			stock_status = frappe._dict({"on_backorder": True})
		else:
			stock_status = get_web_item_qty_in_stock(
				web_item_info.item_code, "website_warehouse"
			)
	item_info = frappe.get_doc("Item", web_item_info.item_code)

	product_info = {
		"details": combined_web_item_info if combine_template else web_item_info,
		"price": price or {},
		"uom": frappe.db.get_value("Item", web_item_info.item_code, "stock_uom"),
		"sales_uom": frappe.db.get_value("Item", web_item_info.item_code, "sales_uom"),
		"attributes": item_info.attributes,
	}

	if web_item_info.slideshow:
		product_info["slideshow"] = frappe.get_doc(
			"Website Slideshow", web_item_info.slideshow
		)

	if stock_status:
		if stock_status.on_backorder:
			product_info["on_backorder"] = True
		else:
			product_info["stock_qty"] = stock_status.stock_qty
			product_info["in_stock"] = (
				stock_status.in_stock
				if stock_status.is_stock_item
				else get_non_stock_item_status(
					web_item_info.item_code, "website_warehouse"
				)
			)
			product_info["show_stock_qty"] = show_quantity_in_website()

	return frappe._dict({"product_info": product_info, "cart_settings": cart_settings})


@frappe.whitelist(allow_guest=True)
def get_item_by_name(name: str, combine_template: bool = False):
	"""
	Get item info by name
	"""

	if not has_permission_for_webshop():
		frappe.throw_permission_error()

	item = frappe.db.get_all("Website Item", filters={"web_item_name": name}, limit=1)
	if item:
		return get_item(item[0].name, combine_template)
	return None


@frappe.whitelist(allow_guest=True)
def get_item_price(item_code: str):
	"""
	Get item price
	"""

	if not has_permission_for_webshop():
		frappe.throw_permission_error()

	cart_settings = get_shopping_cart_settings()
	is_guest = frappe.session.user == "Guest"

	if (
		not cart_settings.enabled
		or not cart_settings.show_price
		or (is_guest and cart_settings.hide_price_for_guest)
	):
		return None

	selling_price_list = _set_price_list(cart_settings, None)
	item_info = frappe.get_cached_doc("Website Item", item_code)
	if item_info.has_variants:
		print("here")
		return None

	price = get_price(
		item_info.item_code,
		selling_price_list,
		cart_settings.default_customer_group,
		cart_settings.company,
	)

	return price


@frappe.whitelist(allow_guest=True)
def get_collection(name: str, raise_redirect=False):
	doc = frappe.get_doc("Website Collection", name)
	if has_permission_for_webshop("Website Collection", doc):
		return doc.as_dict()
	else:
		if raise_redirect:
			frappe.local.flags.redirect_location = "/login"
			raise frappe.Redirect
		else:
			return None


@frappe.whitelist(allow_guest=True)
def get_category(
	name: str, include_subcategory_items: bool = False, raise_redirect: bool = False
):
	doc = frappe.get_doc("Website Category", name)
	if has_permission_for_webshop("Website Category", doc):
		category_doc = doc.as_dict()
		if include_subcategory_items:
			filters = {
				"lft": [">", category_doc.lft],
				"rgt": ["<", category_doc.rgt],
			}
			subcategories = frappe.get_all(
				"Website Category",
				filters=filters,
			)
			items = frappe.get_all(
				"Website Item Table",
				filters={
					"parent": ["in", [d.name for d in subcategories]],
					"parenttype": "Website Category",
				},
				fields=[
					"website_item",
					"item_name",
					"website_image",
					"thumbnail",
					"short_description",
				],
				distinct=True,
			)
			category_doc["subcategory_items"] = items
		return category_doc
	else:
		if raise_redirect:
			frappe.local.flags.redirect_location = "/login"
			raise frappe.Redirect
		else:
			return None


@frappe.whitelist(allow_guest=True)
def list_categories(
	parent: str = "All Website Categories",
	only_immediate_subcategories: bool = False,
	limit: int | None = None,
	start: int = 0,
):
	if not has_permission_for_webshop("Website Categories"):
		frappe.throw_permission_error()

	parent_doc = frappe.get_doc("Website Category", parent)
	filters = {"lft": [">", parent_doc.lft], "rgt": ["<", parent_doc.rgt]}
	if only_immediate_subcategories:
		filters["parent_website_category"] = parent
	categories = frappe.get_all(
		"Website Category",
		filters=filters,
		order_by="lft asc",
		fields=["category_name", "category_image"],
		limit=limit,
		start=start,
	)
	return categories


@frappe.whitelist(allow_guest=True)
def list_collections(limit: int | None = None, start: int = 0):
	if not has_permission_for_webshop("Website Collection"):
		frappe.throw_permission_error()
	collections = frappe.get_all(
		"Website Collection",
		order_by="creation desc",
		fields=["name", "collection_image"],
		limit=limit,
		start=start,
	)
	return collections
