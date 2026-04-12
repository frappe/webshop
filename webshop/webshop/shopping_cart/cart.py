# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import frappe
import frappe.defaults
from frappe import _, throw
from frappe.contacts.doctype.address.address import get_address_display
from frappe.contacts.doctype.contact.contact import get_contact_name
from frappe.utils import cint, cstr, flt, get_fullname
from frappe.utils.nestedset import get_root_of

from erpnext.accounts.utils import get_account_name
from webshop.webshop.doctype.webshop_settings.webshop_settings import (
    get_shopping_cart_settings,
)
from webshop.webshop.utils.product import get_web_item_qty_in_stock
from erpnext.selling.doctype.quotation.quotation import _make_sales_order
from webshop.webshop.shopping_cart.raast_qr import generate_raast_emvco_string


class WebsitePriceListMissingError(frappe.ValidationError):
    pass


def get_target_uom(item_code, customer_group=None):
	"""Determines the default UOM based on the Item Price record in the active price list"""
	cart_settings = get_shopping_cart_settings()
	if not customer_group:
		customer_group = cart_settings.default_customer_group
	
	item_meta = frappe.db.get_value("Item", item_code, ["stock_uom", "sales_uom"], as_dict=True)
	selling_price_list = _set_price_list(cart_settings)

	# Determine preferred UOM
	preferred_uom = item_meta.stock_uom if customer_group == "Retailer" else (item_meta.sales_uom or item_meta.stock_uom)

	# 1. Try to find UOM from Price List with preferred UOM
	uom_from_price = frappe.db.get_value("Item Price", {
		"item_code": item_code,
		"price_list": selling_price_list,
		"uom": preferred_uom
	}, "uom")

	# 2. Fallback to any UOM in this price list
	if not uom_from_price:
		uom_from_price = frappe.db.get_value("Item Price", {
			"item_code": item_code,
			"price_list": selling_price_list
		}, "uom")

	return uom_from_price or preferred_uom


def set_cart_count(quotation=None):
	if cint(frappe.db.get_singles_value("Webshop Settings", "enabled")):
		if not quotation:
			if frappe.session.user == "Guest":
				cart_data = get_guest_cart_quotation()
				quotation = cart_data.get("doc")
			else:
				quotation = _get_cart_quotation()

		cart_count = cstr(cint(quotation.get("total_qty")))

		if hasattr(frappe.local, "cookie_manager"):
			frappe.local.cookie_manager.set_cookie("cart_count", cart_count)


@frappe.whitelist(allow_guest=True)
def get_cart_quotation(doc=None, for_checkout=False, is_cart_page=False):
	if frappe.session.user == "Guest":
		return get_guest_cart_quotation(for_checkout=for_checkout, is_cart_page=is_cart_page)

	party = get_party()
	if not doc:
		quotation = _get_cart_quotation(party)
		doc = quotation
		set_cart_count(quotation)

	addresses = get_address_docs(party=party)
	if not doc.customer_address and addresses:
		update_cart_address("billing", addresses[0].name)

	customer_group = frappe.db.get_value("Customer", party.name, "customer_group")
	
	shipping_method = frappe.cache().get_value(f"shipping_method_{frappe.session.id}") or "Standard"
	
	available_methods = []
	if customer_group == "Retailer":
		available_methods = get_shipping_methods_list(doc.grand_total if doc else 0)

	context = {
		"doc": decorate_quotation_doc(doc),
		"party": party,
		"shipping_addresses": get_shipping_addresses(party),
		"billing_addresses": get_billing_addresses(party),
		"shipping_rules": get_applicable_shipping_rules(party),
		"cart_settings": frappe.get_cached_doc("Webshop Settings"),
		"available_shipping_methods": available_methods,
		"selected_shipping_method": shipping_method
	}

	if for_checkout:
		context.update({
			"items": frappe.render_template("webshop/templates/includes/cart/cart_items.html" if is_cart_page else "webshop/templates/includes/cart/cart_drawer_items.html", context),
			"total": frappe.render_template("webshop/templates/includes/cart/cart_items_total.html", context),
			"taxes_and_totals": frappe.render_template("webshop/templates/includes/cart/cart_drawer_summary.html", context),
		})

	return context

def get_guest_cart_quotation(for_checkout=False, is_cart_page=False):
	cart_items = frappe.cache().get_value(f"cart_{frappe.session.id}") or []
	cart_settings = frappe.get_doc("Webshop Settings")
	shipping_method = frappe.cache().get_value(f"shipping_method_{frappe.session.id}") or "Standard"
	applied_coupon = frappe.cache().get_value(f"applied_coupon_{frappe.session.id}")
	
	doc = frappe.get_doc({
		"doctype": "Quotation",
		"items": [],
		"taxes": [],
		"total_qty": 0,
		"net_total": 0,
		"grand_total": 0,
		"base_grand_total": 0,
		"currency": frappe.get_cached_value("Company", cart_settings.company, "default_currency"),
		"company": cart_settings.company,
		"conversion_rate": 1.0,
		"plc_conversion_rate": 1.0,
		"price_list_currency": frappe.get_cached_value("Company", cart_settings.company, "default_currency"),
		"customer_address": None,
		"shipping_address_name": None,
		"coupon_code": applied_coupon,
		"transaction_date": frappe.utils.today()
	})

	selling_price_list = _set_price_list(cart_settings)

	for item in cart_items:
		item_doc = frappe.get_cached_doc("Website Item", {"item_code": item['item_code']})
		target_uom = item.get('uom') or get_target_uom(item['item_code'])
		
		# Fetch price and UOM from Price List
		price_data = frappe.db.get_value("Item Price", {
			"item_code": item['item_code'],
			"price_list": selling_price_list,
			"uom": target_uom
		}, ["price_list_rate", "uom"], as_dict=True)

		# Fallback to any price in this price list
		if not price_data:
			price_data = frappe.db.get_value("Item Price", {
				"item_code": item['item_code'],
				"price_list": selling_price_list
			}, ["price_list_rate", "uom"], as_dict=True)

		if price_data:
			price = price_data.price_list_rate
			target_uom = price_data.uom
		else:
			price = 0
		
		item_description = item_doc.description or ''
		if item.get('variant_txt'):
			item_description = f'{item_description}<br><b>Variant:</b> {item["variant_txt"]}'

		minimum_qty = frappe.db.get_value("Website Item", {"item_code": item['item_code']}, "minimum_qty") or 1

		item_row = {
			'description': item_description,
			"item_code": item['item_code'],
			"qty": item['qty'],
			"uom": target_uom,
			"rate": flt(price),
			"base_rate": flt(price),
			"amount": flt(item['qty']) * flt(price),
			"base_amount": flt(item['qty']) * flt(price),
			"web_item_name": item_doc.web_item_name,
			"thumbnail": item_doc.thumbnail,
			"minimum_qty": minimum_qty
		}

		# Add Simulated Discount if MRP is missing
		from webshop.webshop.shopping_cart.product_info import calculate_simulated_discount
		
		# Ensure price is handled correctly if it were returned as a tuple/list
		price_val = price[0] if isinstance(price, (list, tuple)) else price
		
		simulated_data = calculate_simulated_discount(item['item_code'], price_val, doc.currency)
		if simulated_data:
			item_row.update(simulated_data)
		
		doc.append("items", item_row)

	# 2. Add Shipping Charge (Sales Taxes and Charges table) - Only for Checkout
	if for_checkout:
		# Use net total before taxes for shipping threshold check
		doc.run_method("calculate_taxes_and_totals")
		methods = get_shipping_methods_list(doc.net_total)
		if methods:
			selected_method = next((m for m in methods if m['name'] == shipping_method), methods[0])
			
			if selected_method and selected_method.get('cost', 0) > 0:
				account_head = cart_settings.get("shipping_account") or "4110 - Sales - VK"
				doc.append("taxes", {
					"charge_type": "Actual",
					"account_head": account_head,
					"description": selected_method['label'],
					"tax_amount": flt(selected_method['cost'])
				})

	# 3. Apply Pricing Rules (Coupons) and final calculation
	doc.ignore_pricing_rule = 0
	doc.run_method("apply_pricing_rule")
	doc.run_method("calculate_taxes_and_totals")

	# Ensure grand_total is updated even if net_total is tiny or 0
	if not doc.grand_total and doc.taxes:
		doc.grand_total = doc.net_total + sum(flt(t.tax_amount) for t in doc.taxes)

	doc.base_grand_total = doc.grand_total
	doc.base_net_total = doc.net_total

	context = {
		"doc": decorate_quotation_doc(doc),
		"shipping_addresses": [],
		"billing_addresses": [],
		"shipping_rules": [],
		"cart_settings": cart_settings,
		"is_guest": True,
		"available_shipping_methods": get_shipping_methods_list(doc.grand_total),
		"selected_shipping_method": shipping_method
	}

	if for_checkout:
		context.update({
			"items": frappe.render_template("webshop/templates/includes/cart/cart_items.html" if is_cart_page else "webshop/templates/includes/cart/cart_drawer_items.html", context),
			"total": frappe.render_template("webshop/templates/includes/cart/cart_items_total.html", context),
			"taxes_and_totals": frappe.render_template("webshop/templates/includes/cart/cart_drawer_summary.html", context),
		})

	return context

@frappe.whitelist(allow_guest=True)
def get_shipping_methods():
	"""Returns available methods based on current Guest Cart total"""
	quotation_data = get_guest_cart_quotation()
	return quotation_data.get("available_shipping_methods", [])

@frappe.whitelist(allow_guest=True)
def set_guest_shipping_method(method):
	"""Stores the guest's shipping choice in cache"""
	frappe.cache().set_value(f"shipping_method_{frappe.session.id}", method, expires_in_sec=86400)
	return {"status": "success"}

def get_shipping_methods_list(cart_total):
	"""Internal helper to calculate shipping based on Webshop Settings"""
	s = frappe.get_doc("Webshop Settings")
	cart_total = flt(cart_total)
	
	threshold = flt(s.get("free_shipping_threshold") or 0)
	is_free = (threshold > 0 and cart_total >= threshold)
	
	methods = []
	if s.get("enable_standard_shipping"):
		methods.append({
			"name": "Standard",
			"label": "Standard Shipping",
			"cost": 0 if is_free else flt(s.get("standard_shipping_charge") or 0)
		})
	if s.get("enable_express_shipping"):
		methods.append({
			"name": "Express",
			"label": "Express Shipping",
			"cost": 0 if is_free else flt(s.get("express_shipping_charge") or 0)
		})
	return methods


@frappe.whitelist()
def get_shipping_addresses(party=None):
	if not party:
		party = get_party()
	addresses = get_address_docs(party=party)
	return [
		{
			"name": address.name,
			"title": address.address_title,
			"display": address.display,
			"is_primary": address.is_primary_address,
			"address_type": address.address_type,
			"address_line1": address.address_line1,
			"city": address.city,
			"state": address.state,
			"country": address.country,
			"pincode": address.pincode,
			"phone": address.phone,
		}
		for address in addresses
	]


@frappe.whitelist()
def get_billing_addresses(party=None):
	if not party:
		party = get_party()
	addresses = get_address_docs(party=party)
	return [
		{
			"name": address.name,
			"title": address.address_title,
			"display": address.display,
		}
		for address in addresses
		if address.address_type == "Billing"
	]


@frappe.whitelist(allow_guest=True)
def get_raast_qr():
	"""Generates a dynamic Raast QR code for the current cart amount"""
	try:
		cart_settings = get_shopping_cart_settings()
		
		if not cart_settings.enable_raast:
			return {"error": "Raast is not enabled in Webshop Settings"}
			
		if not getattr(cart_settings, "raast_id", None):
			return {"error": "Raast ID (Alias/IBAN) is missing in Webshop Settings"}

		# Use get_cart_quotation with for_checkout=True to ensure shipping and taxes are applied
		try:
			context = get_cart_quotation(for_checkout=True)
			quotation = context.get("doc")
		except Exception as e:
			frappe.log_error(f"Error fetching cart for QR: {str(e)}", "Raast QR")
			return {"error": "Error fetching cart total"}

		if not quotation or not getattr(quotation, "grand_total", 0):
			return {"error": "Cart is empty or total is zero"}

		qr_string = generate_raast_emvco_string(
			raast_id=cart_settings.raast_id,
			amount=quotation.grand_total,
			merchant_name=cart_settings.raast_account_title or frappe.defaults.get_global_default("company") or "Webshop"
		)

		if not qr_string:
			return {"error": "Failed to generate QR string"}

		return {
			"qr_string": qr_string,
			"amount": quotation.grand_total,
			"currency": quotation.currency
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Raast QR Generation Error")
		return {"error": str(e)}


@frappe.whitelist(allow_guest=True)
def place_order(quotation_name=None, payment_method=None, receipt_info=None):
	if quotation_name:
		quotation = frappe.get_doc("Quotation", quotation_name)
	else:
		quotation = _get_cart_quotation()
	cart_settings = frappe.get_cached_doc("Webshop Settings")
	quotation.company = cart_settings.company

	quotation.flags.ignore_permissions = True
	quotation.submit()

	if quotation.quotation_to == "Lead" and quotation.party_name:
		# company used to create customer accounts
		frappe.defaults.set_user_default("company", quotation.company)

	if not (quotation.shipping_address_name or quotation.customer_address):
		frappe.throw(_("Set Shipping Address or Billing Address"))

	sales_order = frappe.get_doc(
		_make_sales_order(
			quotation.name, ignore_permissions=True
		)
	)
	sales_order.payment_schedule = []

	if not cint(cart_settings.allow_items_not_in_stock):
		for item in sales_order.get("items"):
			item.warehouse = frappe.db.get_value(
				"Website Item", {"item_code": item.item_code}, "website_warehouse"
			)
			is_stock_item = frappe.db.get_value("Item", item.item_code, "is_stock_item")

			if is_stock_item:
				item_stock = get_web_item_qty_in_stock(
					item.item_code, "website_warehouse"
				)
				if not cint(item_stock.in_stock):
					throw(_("{0} Not in Stock").format(item.item_code))
				if item.qty > item_stock.stock_qty:
					throw(
						_("Only {0} in Stock for item {1}").format(
							item_stock.stock_qty, item.item_code
						)
					)

	if payment_method:
		# Map friendly name to internal gateway and store method for admin visibility
		if payment_method == "COD":
			sales_order.payment_method = "Cash on Delivery"
			sales_order.payment_gateway_account = cart_settings.cod_gateway
		elif payment_method == "Raast":
			sales_order.payment_method = "Raast QR"
			sales_order.payment_gateway_account = cart_settings.raast_gateway
		elif payment_method == "Bank Transfer":
			sales_order.payment_method = "Bank Transfer"
			sales_order.payment_gateway_account = cart_settings.bank_gateway
		else:
			# Native gateway or direct gateway account selection
			sales_order.payment_method = payment_method
			sales_order.payment_gateway_account = payment_method

		# Add a comment for the timeline
		sales_order.add_comment("Comment", _("Checkout Payment Method: {0}").format(sales_order.payment_method))
		
		# For non-immediate/unverified payments, don't auto-submit the SO
		if payment_method in ["COD", "Raast", "Bank Transfer"]:
			sales_order.submit_on_creation = 0
	
	sales_order.flags.ignore_permissions = True
	sales_order.insert()
	sales_order.submit()

	if hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager.delete_cookie("cart_count")

	if receipt_info:
		try:
			from frappe.utils.file_manager import save_file
			import json

			if isinstance(receipt_info, str):
				receipt_info = json.loads(receipt_info)

			filename = receipt_info.get("filename")
			filedata = receipt_info.get("filedata")

			if filename and filedata:
				file_doc = save_file(
					fname=filename,
					content=filedata,
					dt="Sales Order",
					dn=sales_order.name,
					folder="Home/Attachments",
					decode=True,
					is_private=1
				)
				sales_order.add_comment("Comment", _("Payment receipt uploaded: {0}").format(file_doc.file_url))
		except Exception as e:
			frappe.log_error(f"Receipt Attach Error: {str(e)}", "Webshop Checkout")

	return sales_order.name


@frappe.whitelist(allow_guest=True)
def get_order_status(order_id, email):
	"""Returns basic order status for guest tracking"""
	order = frappe.db.get_value("Sales Order", {
		"name": order_id,
		"contact_email": email
	}, ["name", "status", "delivery_status", "grand_total", "currency"], as_dict=True)
	
	if not order:
		frappe.throw(_("Order not found or email mismatch."), frappe.PermissionError)
		
	return order


@frappe.whitelist()
def request_for_quotation():
	quotation = _get_cart_quotation()
	quotation.flags.ignore_permissions = True

	if get_shopping_cart_settings().save_quotations_as_draft:
		quotation.save()
	else:
		quotation.submit()

	return quotation.name


@frappe.whitelist(allow_guest=True)
@frappe.whitelist(allow_guest=True)
def update_cart(item_code, qty, additional_notes=None, with_items=False, uom=None, variant_txt=None):
	if frappe.session.user == "Guest":
		return update_guest_cart(item_code, qty, with_items, uom, variant_txt)

	quotation = _get_cart_quotation()

	empty_card = False
	qty = flt(qty)
	if qty == 0:
		quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
		if quotation_items:
			quotation.set("items", quotation_items)
		else:
			empty_card = True

	else:
		minimum_qty = frappe.db.get_value("Website Item", {"item_code": item_code}, "minimum_qty") or 1
		if qty < minimum_qty:
			qty = minimum_qty

		warehouse = frappe.get_cached_value(
			"Website Item", {"item_code": item_code}, "website_warehouse"
		)

		quotation_items = quotation.get("items", {"item_code": item_code})
		if not quotation_items:
			if not uom:
				uom = get_target_uom(item_code)

			item_doc = frappe.get_cached_doc("Item", item_code)
			description = item_doc.description
			if variant_txt:
				description = f"{description}<br><b>Variant:</b> {variant_txt}"

			quotation.append(
				"items",
				{
					"doctype": "Quotation Item",
					"item_code": item_code,
					"qty": qty,
					"uom": uom,
					"description": description,
					"additional_notes": additional_notes,
					"warehouse": warehouse,
				},
			)
		else:
			quotation_items[0].qty = qty
			if uom:
				quotation_items[0].uom = uom
			
			if variant_txt:
				item_doc = frappe.get_cached_doc("Item", item_code)
				description = item_doc.description
				quotation_items[0].description = f"{description}<br><b>Variant:</b> {variant_txt}"

			quotation_items[0].warehouse = warehouse
			quotation_items[0].additional_notes = additional_notes

	apply_cart_settings(quotation=quotation)

	quotation.flags.ignore_permissions = True
	quotation.payment_schedule = []
	if not empty_card:
		quotation.save()
	else:
		quotation.delete()
		quotation = None

	set_cart_count(quotation)
	
	if cint(with_items):
		is_cart_page = False
		if frappe.request and frappe.request.referrer:
			if "/cart" in frappe.request.referrer:
				is_cart_page = True
		
		context = get_cart_quotation(quotation, for_checkout=True, is_cart_page=is_cart_page)
		return {
			"items": context.get("items"),
			"total": context.get("total"),
			"taxes_and_totals": context.get("taxes_and_totals"),
		}
	else:
		return {"name": quotation.name if quotation else None}

def update_guest_cart(item_code, qty, with_items=0, uom=None, variant_txt=None):
	# Store guest cart in cache
	session_id = frappe.session.id
	cache_key = f"cart_{session_id}"
	cart_items = frappe.cache().get_value(cache_key) or []
	
	qty = flt(qty)
	if qty == 0:
		cart_items = [item for item in cart_items if item['item_code'] != item_code]
	else:
		minimum_qty = frappe.db.get_value("Website Item", {"item_code": item_code}, "minimum_qty") or 1
		if qty < minimum_qty:
			qty = minimum_qty

		if not uom:
			uom = get_target_uom(item_code)

		found = False
		for item in cart_items:
			if item['item_code'] == item_code:
				item['qty'] = qty
				item['uom'] = uom
				if variant_txt:
					item['variant_txt'] = variant_txt
				found = True
				break
		if not found:
			item_data = {'item_code': item_code, 'qty': qty, 'uom': uom}
			if variant_txt:
				item_data['variant_txt'] = variant_txt
			cart_items.append(item_data)
	
	frappe.cache().set_value(cache_key, cart_items, expires_in_sec=86400) # 24 hours
	set_cart_count()

	if cint(with_items):
		is_cart_page = False
		if frappe.request and frappe.request.referrer:
			if "/cart" in frappe.request.referrer:
				is_cart_page = True
				
		context = get_guest_cart_quotation(for_checkout=True, is_cart_page=is_cart_page)
		return {
			"items": context.get("items"),
			"total": context.get("total"),
			"taxes_and_totals": context.get("taxes_and_totals"),
		}
	return {"name": "GuestCart"}


@frappe.whitelist(allow_guest=True)
def convert_guest_cart_to_customer(email, full_name, phone=None, create_account=False, address_data=None, billing_address_data=None):
	"""Converts a guest cart to a real Customer and Quotation, including Address"""
	if frappe.session.user != "Guest":
		return {"status": "success", "message": "User already logged in"}

	# 0. Get Guest Cart Items FIRST (Before any DB operations that might affect session/cache)
	session_id = frappe.session.id
	cache_key = f"cart_{session_id}"
	cart_items = frappe.cache().get_value(cache_key) or []
	
	if not cart_items:
		return {"status": "error", "message": "Cart is empty"}

	# 1. Create User if requested
	if create_account:
		if not frappe.db.exists("User", email):
			try:
				user = frappe.new_doc("User")
				user.email = email
				user.first_name = full_name
				user.enabled = 1
				user.send_welcome_email = 1
				user.append("roles", {"role": "Customer"})
				user.flags.ignore_permissions = True
				user.insert()
			except Exception as e:
				# Log error but don't block order placement
				frappe.log_error(f"Failed to create user at checkout: {str(e)}")

	# 2. Create or Find Customer
	customer_name = frappe.db.get_value("Customer", {"email_id": email})
	if not customer_name:
		try:
			customer = frappe.new_doc("Customer")
			customer.customer_name = full_name
			customer.customer_type = "Individual"
			customer.email_id = email
			customer.mobile_no = phone
			customer.flags.ignore_mandatory = True
			customer.insert(ignore_permissions=True)
			customer_name = customer.name
			frappe.db.commit() # Commit to ensure ID is available for Address/Quotation
		except frappe.DuplicateEntryError:
			customer_name = frappe.db.get_value("Customer", {"email_id": email})
	
	# 2. Add Address if data provided
	shipping_address_name = None
	if address_data:
		if isinstance(address_data, str):
			address_data = frappe.parse_json(address_data)
			
		shipping_address = frappe.new_doc("Address")
		shipping_address.address_title = full_name
		shipping_address.address_type = "Shipping"
		shipping_address.address_line1 = address_data.get("address_line1")
		shipping_address.city = address_data.get("city")
		shipping_address.state = address_data.get("state")
		shipping_address.country = address_data.get("country")
		shipping_address.pincode = address_data.get("pincode")
		shipping_address.phone = phone
		shipping_address.email_id = email
		
		# Link to Customer
		shipping_address.append("links", {
			"link_doctype": "Customer",
			"link_name": customer_name
		})
		
		shipping_address.flags.ignore_permissions = True
		shipping_address.insert()
		shipping_address_name = shipping_address.name

	billing_address_name = shipping_address_name
	if billing_address_data:
		if isinstance(billing_address_data, str):
			billing_address_data = frappe.parse_json(billing_address_data)
			
		billing_address = frappe.new_doc("Address")
		billing_address.address_title = full_name
		billing_address.address_type = "Billing"
		billing_address.address_line1 = billing_address_data.get("address_line1")
		billing_address.city = billing_address_data.get("city")
		billing_address.state = billing_address_data.get("state")
		billing_address.country = billing_address_data.get("country")
		billing_address.pincode = billing_address_data.get("pincode")
		billing_address.phone = phone
		billing_address.email_id = email
		
		# Link to Customer
		billing_address.append("links", {
			"link_doctype": "Customer",
			"link_name": customer_name
		})
		
		billing_address.flags.ignore_permissions = True
		billing_address.insert()
		billing_address_name = billing_address.name

	# 3. Create Quotation for this Customer
	cart_settings = frappe.get_cached_doc("Webshop Settings")
	qdoc = frappe.get_doc({
		"doctype": "Quotation",
		"naming_series": cart_settings.quotation_series or "QTN-CART-",
		"quotation_to": "Customer",
		"party_name": customer_name,
		"customer_address": billing_address_name,
		"shipping_address_name": shipping_address_name,
		"company": cart_settings.company,
		"currency": frappe.get_cached_value("Company", cart_settings.company, "default_currency"),
		"conversion_rate": 1.0,
		"plc_conversion_rate": 1.0,
		"price_list_currency": frappe.get_cached_value("Company", cart_settings.company, "default_currency"),
		"order_type": "Shopping Cart",
		"status": "Draft",
		"contact_email": email
	})

	selling_price_list = _set_price_list(cart_settings)
	qdoc.selling_price_list = selling_price_list

	for item in cart_items:
		warehouse = frappe.get_cached_value("Website Item", {"item_code": item['item_code']}, "website_warehouse")
		
		# Ensure UOM is fetched the same way get_guest_cart_quotation does
		target_uom = item.get('uom') or get_target_uom(item['item_code'])
		
		# Fetch EXACT price using the same fallback logic as the guest cart
		price_data = frappe.db.get_value("Item Price", {
			"item_code": item['item_code'],
			"price_list": selling_price_list,
			"uom": target_uom
		}, ["price_list_rate", "uom"], as_dict=True)

		if not price_data:
			price_data = frappe.db.get_value("Item Price", {
				"item_code": item['item_code'],
				"price_list": selling_price_list
			}, ["price_list_rate", "uom"], as_dict=True)

		price = price_data.price_list_rate if price_data else 0
		if price_data and price_data.uom:
			target_uom = price_data.uom
		
		qdoc.append("items", {
			"item_code": item['item_code'],
			"qty": item['qty'],
			"uom": target_uom,
			"price_list_rate": flt(price),
			"rate": flt(price),
			"warehouse": warehouse
		})

	qdoc.flags.ignore_permissions = True
	qdoc.run_method("set_missing_values")
	
	# Explicitly re-apply pricing rule after set missing values to ensure correct storefront discounts applying
	qdoc.ignore_pricing_rule = 0
	qdoc.run_method("apply_pricing_rule")
	
	# Apply Shipping Method to real Quotation
	shipping_method = frappe.cache().get_value(f"shipping_method_{frappe.session.id}") or "Standard"
	total_before_tax = qdoc.grand_total
	methods = get_shipping_methods_list(total_before_tax)
	selected_method = next((m for m in methods if m['name'] == shipping_method), methods[0])
	
	if selected_method and selected_method.get('cost', 0) > 0:
		qdoc.append("taxes", {
			"charge_type": "Actual",
			"account_head": cart_settings.shipping_account or "4110 - Sales - VK",
			"description": selected_method['label'],
			"tax_amount": flt(selected_method['cost'])
		})
	
	qdoc.run_method("calculate_taxes_and_totals")

	qdoc.save()
	
	# 4. Clear Guest Cache
	frappe.cache().delete_value(cache_key)
	
	return {
		"status": "success",
		"quotation": qdoc.name,
		"customer": customer_name
	}


@frappe.whitelist()
def get_shopping_cart_menu(context=None):
	if not context:
		context = get_cart_quotation()

	return frappe.render_template("templates/includes/cart/cart_dropdown.html", context)


@frappe.whitelist()
def add_new_address(doc):
	doc = frappe.parse_json(doc)
	doc.update({"doctype": "Address"})
	address = frappe.get_doc(doc)
	address.save(ignore_permissions=True)

	return address


@frappe.whitelist(allow_guest=True)
def create_lead_for_item_inquiry(lead, subject, message):
	lead = frappe.parse_json(lead)
	lead_doc = frappe.new_doc("Lead")
	for fieldname in ("lead_name", "company_name", "email_id", "phone"):
		lead_doc.set(fieldname, lead.get(fieldname))

	lead_doc.set("lead_owner", "")

	if not frappe.db.exists("Lead Source", "Product Inquiry"):
		frappe.get_doc(
			{"doctype": "Lead Source", "source_name": "Product Inquiry"}
		).insert(ignore_permissions=True)

	lead_doc.set("source", "Product Inquiry")

	try:
		lead_doc.save(ignore_permissions=True)
	except frappe.exceptions.DuplicateEntryError:
		frappe.clear_messages()
		lead_doc = frappe.get_doc("Lead", {"email_id": lead["email_id"]})

	lead_doc.add_comment(
		"Comment",
		text="""
		<div>
			<h5>{subject}</h5>
			<p>{message}</p>
		</div>
	""".format(
			subject=subject, message=message
		),
	)

	return lead_doc


@frappe.whitelist()
def get_terms_and_conditions(terms_name):
	return frappe.db.get_value("Terms and Conditions", terms_name, "terms")


@frappe.whitelist()
def update_cart_address(address_type, address_name):
	quotation = _get_cart_quotation()
	address_doc = frappe.get_doc("Address", address_name).as_dict()
	address_display = get_address_display(address_doc)

	if address_type.lower() == "billing":
		quotation.customer_address = address_name
		quotation.address_display = address_display
		quotation.shipping_address_name = (
			quotation.shipping_address_name or address_name
		)
		address_doc = next(
			(doc for doc in get_billing_addresses() if doc["name"] == address_name),
			None,
		)
	elif address_type.lower() == "shipping":
		quotation.shipping_address_name = address_name
		quotation.shipping_address = address_display
		quotation.customer_address = quotation.customer_address or address_name
		address_doc = next(
			(doc for doc in get_shipping_addresses() if doc["name"] == address_name),
			None,
		)
	apply_cart_settings(quotation=quotation)

	quotation.flags.ignore_permissions = True
	quotation.save()

	context = get_cart_quotation(quotation)
	context["address"] = address_doc

	return {
		"taxes": frappe.render_template(
			"templates/includes/order/order_taxes.html", context
		),
		"address": frappe.render_template(
			"templates/includes/cart/address_card.html", context
		),
		"taxes_and_totals": frappe.render_template(
			"webshop/templates/includes/cart/checkout_summary_totals.html", context
		),
	}


@frappe.whitelist()
def save_new_address_and_update_cart(address_data):
	"""Saves a new address for a logged-in user and updates their cart quotation"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to save addresses."))

	party = get_party()
	if isinstance(address_data, str):
		address_data = frappe.parse_json(address_data)

	# 1. Create Address
	address = frappe.new_doc("Address")
	address.address_title = address_data.get("address_title") or party.customer_name
	address.address_type = "Shipping"
	address.address_line1 = address_data.get("address_line1")
	address.city = address_data.get("city")
	address.state = address_data.get("state")
	address.country = address_data.get("country")
	address.pincode = address_data.get("pincode")
	address.phone = address_data.get("phone")
	address.email_id = frappe.session.user
	
	address.append("links", {
		"link_doctype": party.doctype,
		"link_name": party.name
	})
	
	address.flags.ignore_permissions = True
	address.insert()
	
	# 2. Update Cart
	return update_cart_address("shipping", address.name)


@frappe.whitelist()
def update_existing_address(address_name, address_data):
	"""Updates an existing address for a logged-in user"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to update addresses."))

	if isinstance(address_data, str):
		address_data = frappe.parse_json(address_data)

	address = frappe.get_doc("Address", address_name)
	
	# Basic ownership check via Dynamic Link
	party = get_party()
	if not any(link.link_name == party.name for link in address.links):
		frappe.throw(_("Not authorized to update this address."))

	address.update({
		"address_line1": address_data.get("address_line1"),
		"city": address_data.get("city"),
		"state": address_data.get("state"),
		"country": address_data.get("country"),
		"pincode": address_data.get("pincode"),
		"phone": address_data.get("phone")
	})
	
	address.flags.ignore_permissions = True
	address.save()
	
	return update_cart_address("shipping", address.name)


@frappe.whitelist()
def delete_existing_address(address_name):
	"""Deletes an existing address for a logged-in user"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to delete addresses."))

	address = frappe.get_doc("Address", address_name)
	
	# Basic ownership check
	party = get_party()
	if not any(link.link_name == party.name for link in address.links):
		frappe.throw(_("Not authorized to delete this address."))

	address.flags.ignore_permissions = True
	address.delete()
	
	return {"status": "success"}


@frappe.whitelist()
def set_address_as_primary(address_name):
	"""Sets an address as primary for the current user's customer"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to manage addresses."))

	party = get_party()
	
	# 1. Unset primary for all addresses linked to this party
	linked_addresses = frappe.db.get_all("Dynamic Link", filters={
		"link_doctype": party.doctype,
		"link_name": party.name,
		"parenttype": "Address"
	}, pluck="parent")

	for addr_name in linked_addresses:
		addr = frappe.get_doc("Address", addr_name)
		if addr.is_primary_address:
			addr.is_primary_address = 0
			addr.flags.ignore_permissions = True
			addr.save()

	# 2. Set primary for the target address
	target_addr = frappe.get_doc("Address", address_name)
	target_addr.is_primary_address = 1
	target_addr.flags.ignore_permissions = True
	target_addr.save()

	return update_cart_address("shipping", address_name)


def guess_territory():
	territory = None
	geoip_country = frappe.session.get("session_country")
	if geoip_country:
		territory = frappe.db.get_value("Territory", geoip_country)

	return (
		territory
		or get_root_of("Territory")
	)


def decorate_quotation_doc(doc):
	for d in doc.get("items", []):
		item_code = d.item_code
		fields = ["web_item_name", "thumbnail", "website_image", "description", "route", "minimum_qty"]

		# Variant Item
		if not frappe.db.exists("Website Item", {"item_code": item_code}):
			variant_data = frappe.db.get_values(
				"Item",
				filters={"item_code": item_code},
				fieldname=["variant_of", "item_name", "image"],
				as_dict=True,
			)[0]
			item_code = variant_data.variant_of
			fields = fields[1:]
			d.web_item_name = variant_data.item_name

			if variant_data.image:  # get image from variant or template web item
				d.thumbnail = variant_data.image
				fields = fields[2:]

		d.update(
			frappe.db.get_value(
				"Website Item", {"item_code": item_code}, fields, as_dict=True
			)
		)

		website_warehouse = frappe.get_cached_value(
			"Website Item", {"item_code": item_code}, "website_warehouse"
		)

		d.warehouse = website_warehouse

		# Add Simulated Discount if MRP is missing
		from webshop.webshop.shopping_cart.product_info import calculate_simulated_discount
		
		simulated_data = calculate_simulated_discount(item_code, d.rate, doc.currency)
		if simulated_data:
			d.update(simulated_data)

	return doc


def _get_cart_quotation(party=None):
	"""Return the open Quotation of type "Shopping Cart" or make a new one"""
	if not party:
		party = get_party()

	quotation = frappe.get_all(
		"Quotation",
		fields=["name"],
		filters={
			"party_name": party.name,
			"contact_email": frappe.session.user,
			"order_type": "Shopping Cart",
			"docstatus": 0,
		},
		order_by="modified desc",
		limit_page_length=1,
	)

	if quotation:
		qdoc = frappe.get_doc("Quotation", quotation[0].name)
	else:
		company = frappe.db.get_single_value("Webshop Settings", "company")
		qdoc = frappe.get_doc(
			{
				"doctype": "Quotation",
				"naming_series": get_shopping_cart_settings().quotation_series
				or "QTN-CART-",
				"quotation_to": party.doctype,
				"company": company,
				"order_type": "Shopping Cart",
				"status": "Draft",
				"docstatus": 0,
				"__islocal": 1,
				"party_name": party.name,
			}
		)

		qdoc.contact_person = frappe.db.get_value(
			"Contact", {"email_id": frappe.session.user}
		)
		qdoc.contact_email = frappe.session.user

		qdoc.flags.ignore_permissions = True
		qdoc.run_method("set_missing_values")
		apply_cart_settings(party, qdoc)

	return qdoc


def update_party(fullname, company_name=None, mobile_no=None, phone=None):
	party = get_party()

	party.customer_name = company_name or fullname
	party.customer_type = "Company" if company_name else "Individual"

	contact_name = frappe.db.get_value("Contact", {"email_id": frappe.session.user})
	contact = frappe.get_doc("Contact", contact_name)
	contact.first_name = fullname
	contact.last_name = None
	contact.customer_name = party.customer_name
	contact.mobile_no = mobile_no
	contact.phone = phone
	contact.flags.ignore_permissions = True
	contact.save()

	party_doc = frappe.get_doc(party.as_dict())
	party_doc.flags.ignore_permissions = True
	party_doc.save()

	qdoc = _get_cart_quotation(party)
	if not qdoc.get("__islocal"):
		qdoc.customer_name = company_name or fullname
		qdoc.run_method("set_missing_lead_customer_details")
		qdoc.flags.ignore_permissions = True
		qdoc.save()


def apply_cart_settings(party=None, quotation=None):
	if not party:
		party = get_party()
	if not quotation:
		quotation = _get_cart_quotation(party)

	cart_settings = frappe.get_cached_doc("Webshop Settings")

	set_price_list_and_rate(quotation, cart_settings)

	quotation.run_method("calculate_taxes_and_totals")

	set_taxes(quotation, cart_settings)

	customer_group = frappe.db.get_value("Customer", party.name, "customer_group")
	if customer_group == "Retailer":
		_apply_shipping_rule(party, quotation, cart_settings)


def set_price_list_and_rate(quotation, cart_settings):
	"""set price list based on billing territory"""

	_set_price_list(cart_settings, quotation)

	# reset values
	quotation.price_list_currency = (
		quotation.currency
	) = quotation.plc_conversion_rate = quotation.conversion_rate = None
	for item in quotation.get("items"):
		item.price_list_rate = item.discount_percentage = item.rate = item.amount = None

	# refetch values
	quotation.run_method("set_price_list_and_item_details")

	if hasattr(frappe.local, "cookie_manager"):
		# set it in cookies for using in product page
		frappe.local.cookie_manager.set_cookie(
			"selling_price_list", quotation.selling_price_list
		)


def _set_price_list(cart_settings, quotation=None):
	"""Set price list based on customer, customer group or shopping cart default"""
	from erpnext.accounts.party import get_default_price_list

	party_name = quotation.get("party_name") if quotation else get_party().get("name")
	selling_price_list = None

	# 1. Check if default customer price list exists
	if party_name and frappe.db.exists("Customer", party_name):
		selling_price_list = get_default_price_list(
			frappe.get_doc("Customer", party_name)
		)

	# 2. Check if default Customer Group price list exists
	if not selling_price_list:
		customer_group = None
		if party_name and frappe.db.exists("Customer", party_name):
			customer_group = frappe.db.get_value("Customer", party_name, "customer_group")
		
		# Fallback to Guest Customer Group from settings if no customer group found
		if not customer_group:
			customer_group = cart_settings.default_customer_group

		if customer_group:
			selling_price_list = frappe.db.get_value("Customer Group", customer_group, "default_price_list")

	# 3. Check default price list in shopping cart
	if not selling_price_list:
		selling_price_list = cart_settings.price_list

	if quotation:
		quotation.selling_price_list = selling_price_list
	
	return selling_price_list

	if quotation:
		quotation.selling_price_list = selling_price_list

	return selling_price_list


def set_taxes(quotation, cart_settings):
	"""set taxes based on billing territory"""
	from erpnext.accounts.party import set_taxes

	customer_group = frappe.db.get_value(
		"Customer", quotation.party_name, "customer_group"
	)

	quotation.taxes_and_charges = set_taxes(
		quotation.party_name,
		"Customer",
		quotation.transaction_date,
		quotation.company,
		customer_group=customer_group,
		supplier_group=None,
		tax_category=quotation.tax_category,
		billing_address=quotation.customer_address,
		shipping_address=quotation.shipping_address_name,
		use_for_shopping_cart=1,
	)
	#
	# 	# clear table
	quotation.set("taxes", [])
	#
	# 	# append taxes
	quotation.append_taxes_from_master()
	quotation.append_taxes_from_item_tax_template()


def get_party(user=None):
	if not user:
		user = frappe.session.user

	contact_name = get_contact_name(user)
	party = None

	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		if contact.links:
			party_doctype = contact.links[0].link_doctype
			party = contact.links[0].link_name

	cart_settings = frappe.get_cached_doc("Webshop Settings")

	debtors_account = ""

	if cart_settings.enable_checkout:
		debtors_account = get_debtors_account(cart_settings)

	if party:
		doc = frappe.get_doc(party_doctype, party)
		if doc.doctype in ["Customer", "Supplier"]:
			if not frappe.db.exists("Portal User", {"parent": doc.name, "user": user}):
				doc.append("portal_users", {"user": user})
				doc.flags.ignore_permissions = True
				doc.flags.ignore_mandatory = True
				doc.save()

		return doc

	elif not frappe.db.exists("Portal User", {"user": user}):
		if not cart_settings.enabled:
			frappe.local.flags.redirect_location = "/contact"
			raise frappe.Redirect
		customer = frappe.new_doc("Customer")
		fullname = get_fullname(user)
		customer.update(
			{
				"customer_name": fullname,
				"customer_type": "Individual",
				"customer_group": get_shopping_cart_settings().default_customer_group,
				"territory": get_root_of("Territory"),
			}
		)

		customer.append("portal_users", {"user": user})

		if debtors_account:
			customer.update(
				{
					"accounts": [
						{"company": cart_settings.company, "account": debtors_account}
					]
				}
			)

		customer.flags.ignore_mandatory = True
		customer.insert(ignore_permissions=True)

		contact = frappe.new_doc("Contact")
		contact.update(
			{"first_name": fullname, "email_ids": [{"email_id": user, "is_primary": 1}]}
		)
		contact.append("links", dict(link_doctype="Customer", link_name=customer.name))
		contact.flags.ignore_mandatory = True
		contact.insert(ignore_permissions=True)

		return customer
	else:
		customer = frappe.db.get_value(
			"Portal User", {"user": user}, ["parent"]
		)

		if frappe.db.exists("Customer", customer):
			return frappe.get_doc("Customer", customer)


def get_debtors_account(cart_settings):
	if not cart_settings.payment_gateway_account:
		frappe.throw(_("Payment Gateway Account not set"), _("Mandatory"))

	payment_gateway_account_currency = frappe.get_doc(
		"Payment Gateway Account", cart_settings.payment_gateway_account
	).currency

	account_name = _("Debtors ({0})").format(payment_gateway_account_currency)

	debtors_account_name = get_account_name(
		"Receivable",
		"Asset",
		is_group=0,
		account_currency=payment_gateway_account_currency,
		company=cart_settings.company,
	)

	if not debtors_account_name:
		debtors_account = frappe.get_doc(
			{
				"doctype": "Account",
				"account_type": "Receivable",
				"root_type": "Asset",
				"is_group": 0,
				"parent_account": get_account_name(
					root_type="Asset", is_group=1, company=cart_settings.company
				),
				"account_name": account_name,
				"currency": payment_gateway_account_currency,
			}
		).insert(ignore_permissions=True)

		return debtors_account.name

	else:
		return debtors_account_name


def get_address_docs(
    doctype=None,
    txt=None,
    filters=None,
    limit_start=0,
    limit_page_length=20,
    party=None,
):
	if not party:
		party = get_party()

	if not party:
		return []

	address_names = frappe.db.get_all(
		"Dynamic Link",
		fields=("parent"),
		filters=dict(
			parenttype="Address", link_doctype=party.doctype, link_name=party.name
		),
	)

	out = []

	for a in address_names:
		address = frappe.get_doc("Address", a.parent)
		address.display = get_address_display(address.as_dict())
		out.append(address)

	return out


@frappe.whitelist()
def apply_shipping_rule(shipping_rule):
	quotation = _get_cart_quotation()

	quotation.shipping_rule = shipping_rule

	apply_cart_settings(quotation=quotation)

	quotation.flags.ignore_permissions = True
	quotation.save()

	return get_cart_quotation(quotation)


def _apply_shipping_rule(party=None, quotation=None, cart_settings=None):
	if not quotation.shipping_rule:
		shipping_rules = get_shipping_rules(quotation, cart_settings)

		if not shipping_rules:
			return

		elif quotation.shipping_rule not in shipping_rules:
			quotation.shipping_rule = shipping_rules[0]

	if quotation.shipping_rule:
		quotation.run_method("apply_shipping_rule")
		quotation.run_method("calculate_taxes_and_totals")


def get_applicable_shipping_rules(party=None, quotation=None):
	shipping_rules = get_shipping_rules(quotation)

	if shipping_rules:
		rule_label_map = frappe.db.get_values("Shipping Rule", shipping_rules, "label")
		# we need this in sorted order as per the position of the rule in the settings page
		return [[rule, rule] for rule in shipping_rules]


def get_shipping_rules(quotation=None, cart_settings=None):
	if not quotation:
		quotation = _get_cart_quotation()

	shipping_rules = []
	if quotation.shipping_address_name:
		country = frappe.db.get_value(
			"Address", quotation.shipping_address_name, "country"
		)
		if country:
			sr_country = frappe.qb.DocType("Shipping Rule Country")
			sr = frappe.qb.DocType("Shipping Rule")
			query = (
				frappe.qb.from_(sr_country)
				.join(sr)
				.on(sr.name == sr_country.parent)
				.select(sr.name)
				.distinct()
				.where((sr_country.country == country) & (sr.disabled != 1) & (sr.shipping_rule_type == "Selling"))
			)
			result = query.run(as_list=True)
			shipping_rules = [x[0] for x in result]

	return shipping_rules


def get_address_territory(address_name):
	"""Tries to match city, state and country of address to existing territory"""
	territory = None

	if address_name:
		address_fields = frappe.db.get_value(
			"Address", address_name, ["city", "state", "country"]
		)
		for value in address_fields:
			territory = frappe.db.get_value("Territory", value)
			if territory:
				break

	return territory


def show_terms(doc):
	return doc.tc_name


@frappe.whitelist(allow_guest=True)
def apply_coupon_code(applied_code, applied_referral_sales_partner=None):
	if not applied_code:
		frappe.throw(_("Please enter a coupon code"))

	coupon_list = frappe.get_all("Coupon Code", filters={"coupon_code": applied_code})
	if not coupon_list:
		frappe.throw(_("Please enter a valid coupon code"))

	coupon_name = coupon_list[0].name

	# Validate coupon using ERPNext logic
	from erpnext.accounts.doctype.pricing_rule.utils import validate_coupon_code
	
	if frappe.session.user == "Guest":
		# For guest, we simulate a quotation to validate
		cart_data = get_guest_cart_quotation()
		doc = cart_data.get("doc")
		
		# Validate coupon against the virtual doc
		validate_coupon_code(doc.name, coupon_name, doc.transaction_date, doc.company, doc.customer)
		
		frappe.cache().set_value(f"applied_coupon_{frappe.session.id}", coupon_name, expires_in_sec=86400)
		return get_guest_cart_quotation()

	quotation = _get_cart_quotation()
	quotation.coupon_code = coupon_name
	validate_coupon_code(quotation.name, coupon_name, quotation.transaction_date, quotation.company, quotation.customer)
	
	quotation.ignore_pricing_rule = 0
	quotation.flags.ignore_permissions = True
	quotation.save()

	if applied_referral_sales_partner:
		sales_partner_list = frappe.get_all(
			"Sales Partner", filters={"referral_code": applied_referral_sales_partner}
		)
		if sales_partner_list:
			sales_partner_name = sales_partner_list[0].name
			quotation.referral_sales_partner = sales_partner_name
			quotation.flags.ignore_permissions = True
			quotation.save()

	return get_cart_quotation(quotation)

 
@frappe.whitelist(allow_guest=True)
def remove_coupon_code():
	if frappe.session.user == "Guest":
		frappe.cache().delete_value(f"applied_coupon_{frappe.session.id}")
		return get_guest_cart_quotation()

	quotation = _get_cart_quotation()
	quotation.coupon_code = ""
	quotation.referral_sales_partner = ""
	quotation.flags.ignore_permissions = True
	quotation.save()
	return quotation

	# reset discount amount if coupon code is removed (on desk it is done in client side)
	# as we are enabling ignore_pricing_rule, so we also need to manually reset discount percentage
	quotation.discount_amount = 0
	quotation.additional_discount_percentage = 0
	quotation.ignore_pricing_rule = 1

	quotation.save()

	return quotation