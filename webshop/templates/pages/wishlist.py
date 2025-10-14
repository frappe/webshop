# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe

from erpnext.utilities.product import get_price as get_base_price
from webshop.webshop.doctype.webshop_settings.webshop_settings import (
	get_shopping_cart_settings,
)
from webshop.webshop.shopping_cart.cart import _set_price_list, get_party
from webshop.webshop.utils.pricing import get_price_for_store
from webshop.webshop.utils.store import get_store_from_cookies


def get_context(context):
	is_guest = frappe.session.user == "Guest"

	settings = get_shopping_cart_settings()
	store = get_store_from_cookies()
	items = get_wishlist_items() if not is_guest else []
	selling_price_list = None
	if not is_guest:
		selling_price_list = (
			store.price_list if store and store.price_list else _set_price_list(settings)
		)

	items = set_stock_price_details(items, settings, selling_price_list, store)

	context.body_class = "product-page"
	context.items = items
	context.settings = settings
	context.no_cache = 1


def get_stock_availability(item_code, warehouse, store_warehouse=None):
	from erpnext.stock.doctype.warehouse.warehouse import get_child_warehouses

	target_warehouse = store_warehouse or warehouse

	if target_warehouse and frappe.get_cached_value("Warehouse", target_warehouse, "is_group") == 1:
		warehouses = get_child_warehouses(target_warehouse)
	else:
		warehouses = [target_warehouse] if target_warehouse else []

	stock_qty = 0.0
	for warehouse in warehouses:
		stock_qty += frappe.utils.flt(
			frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
		)

	return bool(stock_qty)


def get_wishlist_items():
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


def set_stock_price_details(items, settings, selling_price_list, store=None):
	for item in items:
		store_warehouse = store.warehouse if store else None
		store_price_list = store.price_list if store else None

		if settings.show_stock_availability:
			item.available = get_stock_availability(
				item.item_code,
				item.get("warehouse"),
				store_warehouse=store_warehouse,
			)

		party = get_party()

		if store_price_list:
			price_details = get_price_for_store(
				item.item_code,
				store_price_list,
				store_warehouse,
				settings.company,
				settings.default_customer_group,
				party=party,
			)
		else:
			price_details = get_base_price(
				item.item_code,
				selling_price_list,
				settings.default_customer_group,
				settings.company,
				party=party,
			)

		if price_details:
			item.formatted_price = price_details.get("formatted_price")
			item.formatted_mrp = price_details.get("formatted_mrp")
			if item.formatted_mrp:
				item.discount = price_details.get(
					"formatted_discount_percent"
				) or price_details.get("formatted_discount_rate")

	return items
