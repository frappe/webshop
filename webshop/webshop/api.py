# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.utils import cint

from webshop.webshop.doctype.override_doctype.item_group import get_child_groups_for_website
from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.product_data_engine.query import ProductQuery


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
	return frappe.db.get_single_value("Webshop Settings", "redirect_on_action")



@frappe.whitelist(allow_guest=True)
def get_country_state_options(country):
        """Return State/Province suggestions from optional registered providers.

        Providers are registered through the country_state_providers hook.
        Each provider receives a Country name and returns a list of strings
        or dictionaries containing label and value.
        """
        country = str(country or "").strip()
        if not country or len(country) > 140:
                return []

        if not frappe.db.exists("Country", country):
                return []

        providers = frappe.get_hooks("country_state_providers") or []

        for provider_path in providers:
                if not isinstance(provider_path, str) or not provider_path.strip():
                        continue

                try:
                        provider = frappe.get_attr(provider_path)
                        options = provider(country)
                except Exception:
                        frappe.log_error(
                                frappe.get_traceback(),
                                "Webshop country State provider failed",
                        )
                        continue

                if not isinstance(options, (list, tuple)):
                        continue

                result = []
                seen = set()

                for option in options:
                        if isinstance(option, str):
                                label = value = option.strip()
                        elif isinstance(option, dict):
                                label = str(option.get("label") or option.get("value") or "").strip()
                                value = str(option.get("value") or "").strip()
                        else:
                                continue

                        if not value or not label or len(value) > 140 or len(label) > 140:
                                continue

                        key = value.casefold()
                        if key in seen:
                                continue

                        seen.add(key)
                        result.append({"label": label, "value": value})

                if result:
                        return result

        return []
