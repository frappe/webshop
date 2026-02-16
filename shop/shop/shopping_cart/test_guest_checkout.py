# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

import unittest
import frappe
from frappe.tests.utils import change_settings
from shop.shop.shopping_cart.cart import (
	update_cart,
	place_order,
	get_cart_quotation,
	get_party
)

class TestGuestCheckout(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.enable_guest_checkout()

	def tearDown(self):
		frappe.db.rollback()
		frappe.set_user("Administrator")

	def enable_guest_checkout(self):
		settings = frappe.get_doc("Shop Settings")
		settings.update({
			"enabled": 1,
			"allow_guest_checkout": 1,
			"enable_checkout": 1,
			"company": "_Test Company",
			"default_customer_group": "_Test Customer Group",
			"price_list": "_Test Price List India",
			"enable_manual_shipping_charge": 1,
			"default_shipping_charge": 50.0
		})
		settings.save()
		frappe.local.shopping_cart_settings = None

	@change_settings("Shop Settings", {"allow_guest_checkout": 1, "enable_checkout": 1})
	def test_place_order_as_guest(self):
		frappe.set_user("Guest")
		
		# Add item to cart
		update_cart("_Test Item", 1)
		
		guest_details = {
			"email": "guest@example.com",
			"fullname": "Guest User",
			"phone": "1234567890",
			"address": "123 Guest Street, Guest City"
		}
		
		order_name = place_order(guest_details=guest_details)
		self.assertTrue(order_name)
		
		sales_order = frappe.get_doc("Sales Order", order_name)
		self.assertEqual(sales_order.contact_email, "guest@example.com")
		self.assertEqual(sales_order.customer, "Guest Customer")
		
		# Verify shipping charge
		shipping_tax = [t for t in sales_order.taxes if t.description == "Shipping Charge (Manual)"]
		self.assertTrue(shipping_tax)
		self.assertEqual(shipping_tax[0].tax_amount, 50.0)

	@change_settings("Shop Settings", {"enable_manual_shipping_charge": 1, "default_shipping_charge": 100.0})
	def test_manual_shipping_charge(self):
		frappe.set_user("Administrator")
		update_cart("_Test Item", 1)
		
		cart = get_cart_quotation()
		doc = cart.get("doc")
		
		shipping_tax = [t for t in doc.taxes if t.description == "Shipping Charge (Manual)"]
		self.assertTrue(shipping_tax)
		self.assertEqual(shipping_tax[0].tax_amount, 100.0)
