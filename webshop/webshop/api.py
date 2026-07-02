# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website


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
		return {"items": [], "filters": {}, "items_count": 0, "exc": "Something went wrong!"}

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
		"search_recovery": get_search_recovery(search) if search and not result["items"] else {},
	}


def get_search_recovery(search):
	from webshop.templates.pages.product_search import get_search_recovery as build_search_recovery

	return build_search_recovery(search)


@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")


@frappe.whitelist(allow_guest=True)
def get_customer_price_tier():
	from webshop.webshop.shopping_cart.cart import get_customer_price_tier as get_tier

	return get_tier()


@frappe.whitelist(allow_guest=True)
def get_conversion_settings():
	settings = frappe.get_cached_doc("Webshop Settings")
	return {
		"delivery_promise_text": settings.get("delivery_promise_text") or _("Delivery in 2-4 working days"),
		"returns_promise_text": settings.get("returns_promise_text") or _("Easy exchange and support after purchase"),
		"first_order_coupon_code": settings.get("first_order_coupon_code"),
		"first_order_coupon_text": settings.get("first_order_coupon_text"),
		"low_stock_threshold": cint(settings.get("low_stock_threshold") or 5),
		"enable_exit_intent_recovery": 1 if settings.get("enable_exit_intent_recovery") is None else cint(settings.get("enable_exit_intent_recovery")),
		"enable_whatsapp_order": cint(settings.get("enable_whatsapp_order")),
	}


def get_website_item_name(item_code=None, website_item=None):
	if website_item:
		return website_item
	if not item_code:
		return None
	return frappe.db.get_value("Website Item", {"item_code": item_code, "published": 1}, "name")


@frappe.whitelist(allow_guest=True)
def get_item_review_summary(item_code=None, website_item=None):
	website_item = get_website_item_name(item_code=item_code, website_item=website_item)
	if not website_item:
		return {"average_rating": 0, "total_reviews": 0}

	reviews = frappe.get_all(
		"Item Review",
		filters={"website_item": website_item},
		fields=["rating"],
	)
	total_reviews = len(reviews)
	average_rating = sum(flt(review.rating) * 5 for review in reviews) / total_reviews if total_reviews else 0

	return {
		"website_item": website_item,
		"average_rating": flt(average_rating, 1),
		"total_reviews": total_reviews,
	}


def get_storefront_item_details(item_codes=None, item_group=None, exclude_item_codes=None, limit=4):
	from erpnext.utilities.product import get_price
	from webshop.webshop.doctype.webshop_settings.webshop_settings import get_shopping_cart_settings
	from webshop.webshop.shopping_cart.cart import get_customer_price_tier, get_party

	settings = get_shopping_cart_settings()
	tier = get_customer_price_tier(settings)
	party = None if tier.get("is_guest") else get_party()
	filters = {"published": 1}

	if item_codes:
		filters["item_code"] = ["in", item_codes]
	if item_group:
		filters["item_group"] = item_group
	if exclude_item_codes:
		filters["item_code"] = ["not in", exclude_item_codes]

	items = frappe.get_all(
		"Website Item",
		filters=filters,
		fields=[
			"name",
			"web_item_name",
			"item_name",
			"item_code",
			"route",
			"website_image",
			"thumbnail",
			"item_group",
			"website_warehouse as warehouse",
			"ranking",
		],
		order_by="ranking desc, modified desc",
		limit=cint(limit) or 4,
	)

	for item in items:
		price = get_price(
			item.item_code,
			tier.get("price_list"),
			tier.get("customer_group"),
			settings.company,
			party=party,
		)
		if price:
			item.formatted_price = price.get("formatted_price")
			item.formatted_mrp = price.get("formatted_mrp")

		item.review_summary = get_item_review_summary(website_item=item.name)

	return items


@frappe.whitelist(allow_guest=True)
def get_recently_viewed_items(item_codes=None, limit=4):
	if isinstance(item_codes, str):
		item_codes = json.loads(item_codes)
	item_codes = [code for code in (item_codes or []) if code]
	if not item_codes:
		return []

	items = get_storefront_item_details(item_codes=item_codes, limit=limit)
	item_map = {item.item_code: item for item in items}
	return [item_map[code] for code in item_codes if code in item_map]


@frappe.whitelist(allow_guest=True)
def get_smart_recommendations(item_code=None, limit=4):
	exclude = [item_code] if item_code else []
	item_group = frappe.db.get_value("Website Item", {"item_code": item_code}, "item_group") if item_code else None
	items = get_storefront_item_details(item_group=item_group, exclude_item_codes=exclude, limit=limit)
	if not items:
		items = get_storefront_item_details(exclude_item_codes=exclude, limit=limit)
	return items


@frappe.whitelist(allow_guest=True)
def get_cart_whatsapp_assist_url():
	settings = frappe.get_cached_doc("Webshop Settings")
	if not settings.enable_whatsapp_order or not settings.whatsapp_number:
		frappe.throw(_("WhatsApp order number is not configured."))

	from webshop.webshop.shopping_cart.cart import get_cart_quotation

	context = get_cart_quotation(for_checkout=True)
	doc = context.get("doc")
	if not doc or not doc.get("items"):
		frappe.throw(_("Your cart is empty."))

	lines = [_("Hi, I need help with my order:"), ""]
	for item in doc.get("items"):
		lines.append("- {0} x {1}".format(cint(item.qty), item.web_item_name or item.item_name or item.item_code))
	lines.extend([
		"",
		_("Cart total: {0}").format(doc.get_formatted("grand_total")),
		frappe.utils.get_url("/cart"),
	])

	message = "\n".join(lines)
	phone = "".join(ch for ch in settings.whatsapp_number if ch.isdigit())
	return {
		"message": message,
		"url": "https://wa.me/{0}?text={1}".format(phone, quote(message)),
	}


PAYMENT_REVIEW_ROLES = ("System Manager", "Sales Manager", "Accounts Manager", "Accounts User")


def require_payment_reviewer():
	user_roles = set(frappe.get_roles(frappe.session.user))
	if not user_roles.intersection(PAYMENT_REVIEW_ROLES):
		frappe.throw(_("You are not allowed to review webshop payments."), frappe.PermissionError)


@frappe.whitelist()
def get_pending_payment_reviews(limit=50):
	require_payment_reviewer()
	limit = cint(limit) or 50

	return frappe.get_all(
		"Sales Order",
		filters={
			"requires_payment_review": 1,
			"payment_review_status": ["in", ["", "Pending Verification"]],
			"docstatus": 0,
		},
		fields=[
			"name",
			"customer",
			"customer_name",
			"transaction_date",
			"grand_total",
			"currency",
			"payment_method",
			"payment_receipt",
			"payment_review_status",
			"modified",
		],
		order_by="modified desc",
		limit=limit,
	)


@frappe.whitelist()
def approve_payment_review(sales_order, notes=None):
	require_payment_reviewer()
	doc = frappe.get_doc("Sales Order", sales_order)

	if not cint(doc.get("requires_payment_review")):
		frappe.throw(_("This Sales Order does not require payment review."))
	if doc.docstatus != 0:
		frappe.throw(_("Only draft Sales Orders can be approved from payment review."))

	doc.payment_review_status = "Approved"
	doc.payment_review_notes = notes or doc.get("payment_review_notes")
	doc.payment_reviewed_by = frappe.session.user
	doc.payment_reviewed_on = now_datetime()
	# require_payment_reviewer() already restricts this path to trusted payment-review roles.
	# Keep the bypass through submit so reviewers can approve draft webshop orders that they
	# may not otherwise own, while still relying on the review gate and draft/payment checks above.
	doc.flags.ignore_permissions = True
	doc.save()
	doc.add_comment("Comment", _("Payment approved by {0}.").format(frappe.session.user))
	doc.submit()

	return {"name": doc.name, "status": "Approved"}


@frappe.whitelist()
def reject_payment_review(sales_order, notes=None):
	require_payment_reviewer()
	if not notes:
		frappe.throw(_("Please add a reason before rejecting the payment."))

	doc = frappe.get_doc("Sales Order", sales_order)
	if not cint(doc.get("requires_payment_review")):
		frappe.throw(_("This Sales Order does not require payment review."))
	if doc.docstatus != 0:
		frappe.throw(_("Only draft Sales Orders can be rejected from payment review."))

	doc.payment_review_status = "Rejected"
	doc.payment_review_notes = notes
	doc.payment_reviewed_by = frappe.session.user
	doc.payment_reviewed_on = now_datetime()
	doc.flags.ignore_permissions = True
	doc.save()
	doc.add_comment("Comment", _("Payment rejected by {0}: {1}").format(frappe.session.user, notes))

	return {"name": doc.name, "status": "Rejected"}


@frappe.whitelist(allow_guest=True)
def get_product_bundles(item_code, limit=4):
	if not item_code:
		return []

	bundle_names = set(frappe.get_all(
		"Product Bundle",
		filters={"new_item_code": item_code},
		pluck="name",
	))
	bundle_names.update(
		row.parent for row in frappe.get_all(
			"Product Bundle Item",
			filters={"item_code": item_code},
			fields=["parent"],
		)
	)
	if not bundle_names:
		return []

	from erpnext.utilities.product import get_price
	from webshop.webshop.doctype.webshop_settings.webshop_settings import get_shopping_cart_settings
	from webshop.webshop.shopping_cart.cart import get_customer_price_tier, get_party

	settings = get_shopping_cart_settings()
	tier = get_customer_price_tier(settings)
	party = None if tier.get("is_guest") else get_party()
	limit = cint(limit) or 4

	bundles = []
	for bundle_name in list(bundle_names)[:limit]:
		bundle = frappe.get_doc("Product Bundle", bundle_name)
		web_item = frappe.db.get_value(
			"Website Item",
			{"item_code": bundle.new_item_code, "published": 1},
			[
				"name",
				"web_item_name",
				"item_name",
				"item_code",
				"route",
				"website_image as image",
			],
			as_dict=True,
		)
		if not web_item:
			continue
		web_item.website_item = web_item.name

		price = get_price(
			bundle.new_item_code,
			tier.get("price_list"),
			tier.get("customer_group"),
			settings.company,
			party=party,
		)
		components = []
		for row in bundle.get("items"):
			components.append({
				"item_code": row.item_code,
				"item_name": frappe.db.get_value("Item", row.item_code, "item_name") or row.item_code,
				"qty": row.qty,
			})

		web_item.update({
			"bundle": bundle.name,
			"description": bundle.description,
			"components": components,
			"formatted_price": price.get("formatted_price") if price else None,
			"formatted_mrp": price.get("formatted_mrp") if price else None,
		})
		bundles.append(web_item)

	return bundles


@frappe.whitelist(allow_guest=True)
def get_wishlist_items_details(item_codes):
	if isinstance(item_codes, str):
		item_codes = json.loads(item_codes)

	if not item_codes:
		return []

	from erpnext.utilities.product import get_price
	from webshop.webshop.doctype.webshop_settings.webshop_settings import get_shopping_cart_settings
	from webshop.webshop.shopping_cart.cart import _set_price_list, get_party

	settings = get_shopping_cart_settings()
	customer_group = settings.default_customer_group

	if frappe.session.user == "Guest":
		customer_group = settings.guest_customer_group or settings.default_customer_group
		selling_price_list = (
			settings.guest_price_list
			or frappe.db.get_value("Customer Group", customer_group, "default_price_list")
			or settings.price_list
		)
		party = None
	else:
		party = get_party()
		customer_group = frappe.db.get_value("Customer", party.name, "customer_group") or customer_group
		selling_price_list = _set_price_list(settings)

	items = frappe.get_all(
		"Website Item",
		filters={"item_code": ["in", item_codes]},
		fields=[
			"web_item_name",
			"item_code",
			"item_name",
			"name as website_item",
			"website_warehouse as warehouse",
			"website_image as image",
			"item_group",
			"route",
		],
	)

	# Fetch price and stock details
	for item in items:
		price_details = get_price(
			item.item_code,
			selling_price_list,
			customer_group,
			settings.company,
			party=party,
		)

		if price_details:
			item.formatted_price = price_details.get("formatted_price")
			item.formatted_mrp = price_details.get("formatted_mrp")
			if item.formatted_mrp:
				item.discount = price_details.get("formatted_discount_percent") or price_details.get("formatted_discount_rate")

		# Stock availability
		if settings.show_stock_availability:
			from webshop.templates.pages.wishlist import get_stock_availability
			item.available = get_stock_availability(item.item_code, item.warehouse)
		else:
			item.available = True

	return items


@frappe.whitelist()
def get_wishlist_whatsapp_quote():
	settings = frappe.get_cached_doc("Webshop Settings")
	if not settings.enable_whatsapp_order or not settings.whatsapp_number:
		frappe.throw(_("WhatsApp order number is not configured."))

	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to send your wishlist on WhatsApp."), frappe.PermissionError)

	items = get_wishlist_items_details([
		item.item_code for item in frappe.get_all(
			"Wishlist Item",
			filters={"parent": frappe.session.user},
			fields=["item_code"],
		)
	])
	if not items:
		frappe.throw(_("Your wishlist is empty."))

	lines = [_("*Wishlist Quote Request*"), "", _("Hi, I would like a quote for these items:"), ""]
	for item in items:
		price = item.get("formatted_price") or _("Price on request")
		lines.append("• {0} ({1}) - {2}".format(item.get("web_item_name") or item.get("item_name"), item.item_code, price))

	lines.extend(["", _("Customer: {0}").format(frappe.session.user)])
	message = "\n".join(lines)
	phone = "".join(ch for ch in settings.whatsapp_number if ch.isdigit())

	return {
		"message": message,
		"url": "https://wa.me/{0}?text={1}".format(phone, quote(message)),
	}
