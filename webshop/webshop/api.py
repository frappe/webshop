# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import cint

from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery
from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website


@frappe.whitelist(allow_guest=True)
def get_product_filter_data(query_args=None):
    # Parse query arguments
    if isinstance(query_args, str):
        query_args = json.loads(query_args)
    query_args = frappe._dict(query_args or {})

    # Extract filters
    search = query_args.get("search")
    field_filters = query_args.get("field_filters", {})
    attribute_filters = query_args.get("attribute_filters", {})
    start = cint(query_args.start) if query_args.get("start") else 0
    item_group = query_args.get("item_group")
    from_filters = query_args.get("from_filters")

    if from_filters:
        start = 0

    sub_categories = []
    if item_group:
        sub_categories = get_child_groups_for_website(item_group, immediate=True)

    engine = ProductQuery()

    # Query products
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

    # Build discount filters
    filters = {}
    discounts = result.get("discounts", [])
    if discounts:
        filter_engine = ProductFiltersBuilder()
        filters["discount_filters"] = filter_engine.get_discount_filters(discounts)

    # Add qty_in_cart to items
    customer = get_customer(silent=True)
    cart_qty_map = get_cart_qty_map(customer) if customer else {}

    for item in result.get("items", []):
        item["qty_in_cart"] = cart_qty_map.get(item.get("item_code"), 0)

    # Return the final result
    return {
        "items": result["items"] or [],
        "filters": filters,
        "settings": engine.settings,
        "sub_categories": sub_categories,
        "items_count": result.get("items_count", 0),
    }


from webshop.webshop.doctype.item_review.item_review import get_customer
@frappe.whitelist(allow_guest=True)
def get_cart_qty_map(customer):
    """Fetch all quantities in the customer's draft cart and return a mapping."""
    quotation = frappe.get_all(
        "Quotation",
        fields=["name"],
        filters={
            "party_name": customer,
            "contact_email": frappe.session.user,
            "order_type": "Shopping Cart",
            "docstatus": 0,
        },
        order_by="modified desc",
        limit_page_length=1,
    )

    if quotation:
        items = frappe.db.sql(
            """
            SELECT item_code, SUM(qty) as qty
            FROM `tabQuotation Item`
            WHERE parent = %s
            GROUP BY item_code
            """,
            (quotation[0]["name"],),
            as_dict=True,
        )
        return {item["item_code"]: item["qty"] for item in items}
    return {}



@frappe.whitelist(allow_guest=True)
def get_guest_redirect_on_action():
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")
