# GLOBAL SIMULATED DISCOUNT CONFIGURATION
# Set this value (e.g. 40, 50, etc.) to change the global sale percentage.
# Individual Website Items can override this if they have a 'simulated_discount' custom field.
GLOBAL_SIMULATED_DISCOUNT_PERCENTAGE = 40

import frappe
from erpnext.utilities.product import get_price

from webshop.webshop.doctype.webshop_settings.webshop_settings import (
    get_shopping_cart_settings,
    show_quantity_in_website,
)
from erpnext.utilities.product import (get_price)
from webshop.webshop.utils.product import (get_non_stock_item_status, get_web_item_qty_in_stock)


@frappe.whitelist(allow_guest=True)
def get_product_info_for_website(item_code, skip_quotation_creation=False):
	"""
	Get product price / stock info for website
	"""
	from webshop.webshop.shopping_cart.cart import _get_cart_quotation, _set_price_list, get_party

	cart_settings = get_shopping_cart_settings()
	if not cart_settings.enabled:
		# return settings even if cart is disabled
		return frappe._dict({"product_info": {}, "cart_settings": cart_settings})

	cart_quotation = frappe._dict()
	if not skip_quotation_creation:
		cart_quotation = _get_cart_quotation()

	selling_price_list = (
		cart_quotation.get("selling_price_list")
		if cart_quotation
		else _set_price_list(cart_settings, None)
	)

	price = {}
	target_uom = None
	item_meta = frappe.db.get_value("Item", item_code, ["stock_uom", "sales_uom"], as_dict=True)

	if cart_settings.show_price:
		is_guest = frappe.session.user == "Guest"
		party = get_party()
		
		# Determine Customer Group
		customer_group = None
		if party and party.customer_group:
			customer_group = party.customer_group
		else:
			customer_group = cart_settings.default_customer_group
		
		# Determine preferred UOM
		preferred_uom = item_meta.stock_uom if customer_group == "Retailer" else (item_meta.sales_uom or item_meta.stock_uom)

		# Show Price if logged in.
		# If not logged in, check if price is hidden for guest.
		if not is_guest or not cart_settings.hide_price_for_guest:
			# 1. Try to get price for preferred UOM
			uom_price = frappe.db.get_value("Item Price", {
				"item_code": item_code,
				"price_list": selling_price_list,
				"uom": preferred_uom
			}, ["price_list_rate", "currency", "uom"], as_dict=True)

			# 2. Fallback to any price in this price list if preferred UOM not found
			if not uom_price:
				uom_price = frappe.db.get_value("Item Price", {
					"item_code": item_code,
					"price_list": selling_price_list
				}, ["price_list_rate", "currency", "uom"], as_dict=True)

			if uom_price:
				target_uom = uom_price.uom
				price = {
					"price_list_rate": uom_price.price_list_rate,
					"currency": uom_price.currency,
					"formatted_price": frappe.format(uom_price.price_list_rate, {"fieldtype": "Currency", "currency": uom_price.currency}),
					"formatted_price_sales_uom": frappe.format(uom_price.price_list_rate, {"fieldtype": "Currency", "currency": uom_price.currency})
				}
			else:
				# 3. Last fallback: ERPNext standard get_price (might return nothing if no Item Price exists)
				price = get_price(
					item_code,
					selling_price_list,
					customer_group,
					cart_settings.company,
					party=party,
				)
				if price:
					target_uom = price.get("uom") or item_meta.stock_uom

			# Apply Simulated Discount if MRP is missing
			if price:
				# Ensure price is a dictionary (ERPNext get_price can sometimes return a tuple in specific versions)
				if isinstance(price, (list, tuple)):
					price = frappe._dict({"price_list_rate": price[0], "currency": price[1] if len(price) > 1 else None})
				
				if not price.get("formatted_mrp"):
					simulated_data = calculate_simulated_discount(item_code, price.get("price_list_rate"), price.get("currency"))
					if simulated_data:
						price.update(simulated_data)

	if not target_uom:
		target_uom = item_meta.sales_uom or item_meta.stock_uom

	stock_status = None

	if cart_settings.show_stock_availability:
		on_backorder = frappe.get_cached_value(
			"Website Item", {"item_code": item_code}, "on_backorder"
		)
		if on_backorder:
			stock_status = frappe._dict({"on_backorder": True})
		else:
			stock_status = get_web_item_qty_in_stock(item_code, "website_warehouse")

	product_info = {
		"price": price,
		"qty": 0,
		"uom": target_uom,
		"stock_uom": item_meta.stock_uom,
		"sales_uom": item_meta.sales_uom,
	}

	if stock_status:
		if stock_status.on_backorder:
			product_info["on_backorder"] = True
		else:
			product_info["stock_qty"] = stock_status.stock_qty
			product_info["in_stock"] = (
				stock_status.in_stock
				if stock_status.is_stock_item
				else get_non_stock_item_status(item_code, "website_warehouse")
			)
			product_info["show_stock_qty"] = show_quantity_in_website()

	if product_info["price"]:
		if frappe.session.user != "Guest":
			item = (
				cart_quotation.get({"item_code": item_code}) if cart_quotation else None
			)
			if item:
				product_info["qty"] = item[0].qty

	return frappe._dict({
		"product_info": product_info, 
		"cart_settings": cart_settings,
		"customer_group": customer_group,
		"is_guest": is_guest
	})


def set_product_info_for_website(item):
	"""set product price uom for website"""
	product_info = get_product_info_for_website(
		item.item_code, skip_quotation_creation=True
	).get("product_info")

	if product_info:
		item.update(product_info)
		item["stock_uom"] = product_info.get("uom")
		item["sales_uom"] = product_info.get("sales_uom")
		if product_info.get("price"):
			item["price_stock_uom"] = product_info.get("price").get("formatted_price")
			item["price_sales_uom"] = product_info.get("price").get(
				"formatted_price_sales_uom"
			)
		else:
			item["price_stock_uom"] = ""
			item["price_sales_uom"] = ""

def calculate_simulated_discount(item_code, price_rate, currency):
	"""Calculates MRP and discount percent based on hierarchy:
	1. Website Offer child table (if entry exists)
	2. Website Item 'simulated_discount' field
	3. Global default (40%)
	"""
	from frappe.utils import flt
	import re

	discount_percent = 0
	offer_title = None

	# 1. Check Website Offer Child Table
	offers = []
	website_item = frappe.db.get_value("Website Item", {"item_code": item_code}, "name")
	if website_item:
		offers = frappe.get_all("Website Offer", 
			filters={"parent": website_item},
			fields=["offer_title"],
			order_by="idx asc",
			limit=1
		)

	if offers:
		offer_title = offers[0].offer_title
		# Try to extract percentage from title (e.g. "20% off" -> 20)
		match = re.search(r"(\d+)\s*%", offer_title)
		if match:
			discount_percent = flt(match.group(1))

	# Determine if user is Retailer or Guest to allow promotional fallbacks
	is_retailer = True
	if getattr(frappe.session, "user", "Guest") != "Guest":
		# Direct DB lookup to avoid circular import with cart.py
		# Find the Customer linked to this Portal User
		customer = frappe.db.get_value("Portal User", {"user": frappe.session.user}, "parent")
		if customer:
			customer_group = frappe.db.get_value("Customer", customer, "customer_group")
		
		# Allow non-Retailer users (like wholesale) to still see basic price logic if needed,
		# but here we disable promotional fallbacks for them.
		if customer_group and customer_group != "Retailer":
			is_retailer = False

	# 2. Fallback to Item-specific 'simulated_discount' field if no percentage from offer
	if not discount_percent and is_retailer:
		try:
			website_item_data = frappe.db.get_value("Website Item", {"item_code": item_code}, ["simulated_discount"], as_dict=True)
			if website_item_data:
				discount_percent = website_item_data.get("simulated_discount") or 0
		except Exception:
			discount_percent = 0

	# 3. Fallback to Global Default from Settings
	if not discount_percent and is_retailer:
		try:
			# Check if global default is enabled
			enable_global = frappe.db.get_single_value("Webshop Settings", "enable_global_simulated_discount")
			if not enable_global:
				return None

			# Use a localized fetch to avoid circular imports if needed
			settings_discount = frappe.db.get_single_value("Webshop Settings", "simulated_discount_percentage")
			if settings_discount is not None:
				global_default = settings_discount
			else:
				global_default = GLOBAL_SIMULATED_DISCOUNT_PERCENTAGE
		except Exception:
			global_default = 40.0
			
		discount_percent = flt(global_default)

	discount_percent = flt(discount_percent)
	
	if not currency:
		# Fallback currency from Webshop Settings or Company
		currency = frappe.db.get_single_value("Webshop Settings", "default_currency") or \
				   frappe.db.get_single_value("Global Defaults", "default_currency") or "USD"

	if 0 < discount_percent < 100:
		# Calculate MRP: price = MRP * (1 - discount/100) -> MRP = price / (1 - discount/100)
		mrp = flt(price_rate) / (1 - (discount_percent / 100.0))
		
		res = {
			"mrp": mrp,
			"formatted_mrp": frappe.format(mrp, {"fieldtype": "Currency", "currency": currency}),
			"discount_percent": discount_percent,
			"formatted_discount_percent": offer_title if offer_title else f"{int(discount_percent)}% OFF"
		}
		
		# Override if offer exists but didn't have a percentage (no MRP calculation possible)
		if offers and not re.search(r"(\d+)\s*%", offers[0].offer_title):
			res.pop("mrp", None)
			res.pop("formatted_mrp", None)
			
		return res
		
	elif offers and offers[0].offer_title:
		# Offer exists but NO percentage and NO fallback discount possible
		return {
			"formatted_discount_percent": offers[0].offer_title
		}

	return None
