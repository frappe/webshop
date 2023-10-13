# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import unittest

import frappe

from erpnext.controllers.item_variant import create_variant
from webshop.webshop.doctype.webshop_settings.webshop_settings import (
	get_shopping_cart_settings,
)
from webshop.webshop.doctype.webshop_settings.test_webshop_settings import (
	setup_webshop_settings,
)
from webshop.webshop.doctype.website_item.website_item import make_website_item
from webshop.webshop.shopping_cart.product_info import get_product_info_for_website
from erpnext.stock.doctype.item.item import DataValidationError
from erpnext.stock.doctype.item.test_item import make_item

WEBITEM_DESK_TESTS = ("test_website_item_desk_item_sync", "test_publish_variant_and_template")
WEBITEM_PRICE_TESTS = (
	"test_website_item_price_for_logged_in_user",
	"test_website_item_price_for_guest_user",
)


class TestWebsiteItem(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		setup_webshop_settings(
			{
				"company": "_Test Company",
				"enabled": 1,
				"default_customer_group": "_Test Customer Group",
				"price_list": "_Test Price List India",
			}
		)

	@classmethod
	def tearDownClass(cls):
		frappe.db.rollback()

	def setUp(self):
		if self._testMethodName in WEBITEM_DESK_TESTS:
			make_item(
				"Test Web Item",
				{
					"has_variant": 1,
					"variant_based_on": "Item Attribute",
					"attributes": [{"attribute": "Test Size"}],
				},
			)
		elif self._testMethodName in WEBITEM_PRICE_TESTS:
			create_user_and_customer_if_not_exists(
				"test_contact_customer@example.com", "_Test Contact For _Test Customer"
			)
			create_regular_web_item()
			make_web_item_price(item_code="Test Mobile Phone")

			# Note: When testing web item pricing rule logged-in user pricing rule must differ from guest pricing rule or test will falsely pass.
			# 	  This is because make_web_pricing_rule creates a pricing rule "selling": 1, without specifying "applicable_for". Therefor,
			# 	  when testing for logged-in user the test will get the previous pricing rule because "selling" is still true.
			#
			#     I've attempted to mitigate this by setting applicable_for=Customer, and customer=Guest however, this only results in PermissionError failing the test.
			make_web_pricing_rule(
				title="Test Pricing Rule for Test Mobile Phone", item_code="Test Mobile Phone", selling=1
			)
			make_web_pricing_rule(
				title="Test Pricing Rule for Test Mobile Phone (Customer)",
				item_code="Test Mobile Phone",
				selling=1,
				discount_percentage="25",
				applicable_for="Customer",
				customer="_Test Customer",
			)

	def test_index_creation(self):
		"Check if index is getting created in db."
		from webshop.webshop.doctype.website_item.website_item import on_doctype_update

		on_doctype_update()

		indices = frappe.db.sql("show index from `tabWebsite Item`", as_dict=1)
		expected_columns = {"route", "item_group", "brand"}
		for index in indices:
			expected_columns.discard(index.get("Column_name"))

		if expected_columns:
			self.fail(f"Expected db index on these columns: {', '.join(expected_columns)}")

	def test_website_item_desk_item_sync(self):
		"Check creation/updation/deletion of Website Item and its impact on Item master."
		web_item = None
		item = make_item("Test Web Item")  # will return item if exists
		try:
			web_item = make_website_item(item, save=False)
			web_item.save()
		except Exception:
			self.fail(f"Error while creating website item for {item}")

		# check if website item was created
		self.assertTrue(bool(web_item))
		self.assertTrue(bool(web_item.route))

		item.reload()
		self.assertEqual(web_item.published, 1)
		self.assertEqual(item.published_in_website, 1)  # check if item was back updated
		self.assertEqual(web_item.item_group, item.item_group)

		# check if changing item data changes it in website item
		item.item_name = "Test Web Item 1"
		item.stock_uom = "Unit"
		item.save()
		web_item.reload()
		self.assertEqual(web_item.item_name, item.item_name)
		self.assertEqual(web_item.stock_uom, item.stock_uom)

		# check if disabling item unpublished website item
		item.disabled = 1
		item.save()
		web_item.reload()
		self.assertEqual(web_item.published, 0)

		# check if website item deletion, unpublishes desk item
		web_item.delete()
		item.reload()
		self.assertEqual(item.published_in_website, 0)

		item.delete()

	def test_publish_variant_and_template(self):
		"Check if template is published on publishing variant."
		# template "Test Web Item" created on setUp
		variant = create_variant("Test Web Item", {"Test Size": "Large"})
		variant.save()

		# check if template is not published
		self.assertIsNone(frappe.db.exists("Website Item", {"item_code": variant.variant_of}))

		variant_web_item = make_website_item(variant, save=False)
		variant_web_item.save()

		# check if template is published
		try:
			template_web_item = frappe.get_doc("Website Item", {"item_code": variant.variant_of})
		except frappe.DoesNotExistError:
			self.fail(f"Template of {variant.item_code}, {variant.variant_of} not published")

		# teardown
		variant_web_item.delete()
		template_web_item.delete()
		variant.delete()

	def test_impact_on_merging_items(self):
		"Check if merging items is blocked if old and new items both have website items"
		first_item = make_item("Test First Item")
		second_item = make_item("Test Second Item")

		first_web_item = make_website_item(first_item, save=False)
		first_web_item.save()
		second_web_item = make_website_item(second_item, save=False)
		second_web_item.save()

		with self.assertRaises(DataValidationError):
			frappe.rename_doc("Item", "Test First Item", "Test Second Item", merge=True)

		# tear down
		second_web_item.delete()
		first_web_item.delete()
		second_item.delete()
		first_item.delete()

	# Website Item Portal Tests Begin

	def test_website_item_breadcrumbs(self):
		"Check if breadcrumbs include homepage, product listing navigation page, parent item group(s) and item group."
		from erpnext.setup.doctype.item_group.item_group import get_parent_item_groups

		item_code = "Test Breadcrumb Item"
		item = make_item(
			item_code,
			{
				"item_group": "_Test Item Group B - 1",
			},
		)

		if not frappe.db.exists("Website Item", {"item_code": item_code}):
			web_item = make_website_item(item, save=False)
			web_item.save()
		else:
			web_item = frappe.get_cached_doc("Website Item", {"item_code": item_code})

		frappe.db.set_value("Item Group", "_Test Item Group B - 1", "show_in_website", 1)
		frappe.db.set_value("Item Group", "_Test Item Group B", "show_in_website", 1)

		breadcrumbs = get_parent_item_groups(item.item_group)

		self.assertEqual(breadcrumbs[0]["name"], "Home")
		self.assertEqual(breadcrumbs[1]["name"], "Shop by Category")
		self.assertEqual(breadcrumbs[2]["name"], "_Test Item Group B")  # parent item group
		self.assertEqual(breadcrumbs[3]["name"], "_Test Item Group B - 1")

		# tear down
		web_item.delete()
		item.delete()

	def test_website_item_price_for_logged_in_user(self):
		"Check if price details are fetched correctly while logged in."
		item_code = "Test Mobile Phone"

		# show price in webshop settings
		setup_webshop_settings({"show_price": 1})

		# price and pricing rule added via setUp

		# login as customer with pricing rule
		frappe.set_user("test_contact_customer@example.com")

		# check if price and slashed price is fetched correctly
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertTrue(bool(data.product_info["price"]))

		price_object = data.product_info["price"]
		self.assertEqual(price_object.get("discount_percent"), 25)
		self.assertEqual(price_object.get("price_list_rate"), 750)
		self.assertEqual(price_object.get("formatted_mrp"), "₹ 1,000.00")
		self.assertEqual(price_object.get("formatted_price"), "₹ 750.00")
		self.assertEqual(price_object.get("formatted_discount_percent"), "25%")

		# switch to admin and disable show price
		frappe.set_user("Administrator")
		setup_webshop_settings({"show_price": 0})

		# price should not be fetched for logged in user.
		frappe.set_user("test_contact_customer@example.com")
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertFalse(bool(data.product_info["price"]))

		# tear down
		frappe.set_user("Administrator")

	def test_website_item_price_for_guest_user(self):
		"Check if price details are fetched correctly for guest user."
		item_code = "Test Mobile Phone"

		# show price for guest user in webshop settings
		setup_webshop_settings({"show_price": 1, "hide_price_for_guest": 0})

		# price and pricing rule added via setUp

		# switch to guest user
		frappe.set_user("Guest")

		# price should be fetched
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertTrue(bool(data.product_info["price"]))

		price_object = data.product_info["price"]
		self.assertEqual(price_object.get("discount_percent"), 10)
		self.assertEqual(price_object.get("price_list_rate"), 900)

		# hide price for guest user
		frappe.set_user("Administrator")
		setup_webshop_settings({"hide_price_for_guest": 1})
		frappe.set_user("Guest")

		# price should not be fetched
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertFalse(bool(data.product_info["price"]))

		# tear down
		frappe.set_user("Administrator")

	def test_website_item_stock_when_out_of_stock(self):
		"""
		Check if stock details are fetched correctly for empty inventory when:
		1) Showing stock availability enabled:
		        - Warehouse unset
		        - Warehouse set
		2) Showing stock availability disabled
		"""
		item_code = "Test Mobile Phone"
		create_regular_web_item()
		setup_webshop_settings({"show_stock_availability": 1})

		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)

		# check if stock details are fetched and item not in stock without warehouse set
		self.assertFalse(bool(data.product_info["in_stock"]))
		self.assertFalse(bool(data.product_info["stock_qty"]))

		# set warehouse
		frappe.db.set_value(
			"Website Item", {"item_code": item_code}, "website_warehouse", "_Test Warehouse - _TC"
		)

		# check if stock details are fetched and item not in stock with warehouse set
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertFalse(bool(data.product_info["in_stock"]))
		self.assertEqual(data.product_info["stock_qty"], 0)

		# disable show stock availability
		setup_webshop_settings({"show_stock_availability": 0})
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)

		# check if stock detail attributes are not fetched if stock availability is hidden
		self.assertIsNone(data.product_info.get("in_stock"))
		self.assertIsNone(data.product_info.get("stock_qty"))
		self.assertIsNone(data.product_info.get("show_stock_qty"))

		# tear down
		frappe.get_cached_doc("Website Item", {"item_code": "Test Mobile Phone"}).delete()

	def test_website_item_stock_when_in_stock(self):
		"""
		Check if stock details are fetched correctly for available inventory when:
		1) Showing stock availability enabled:
		        - Warehouse set
		        - Warehouse unset
		2) Showing stock availability disabled
		"""
		from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry

		item_code = "Test Mobile Phone"
		create_regular_web_item()
		setup_webshop_settings({"show_stock_availability": 1})
		frappe.local.shopping_cart_settings = None

		# set warehouse
		frappe.db.set_value(
			"Website Item", {"item_code": item_code}, "website_warehouse", "_Test Warehouse - _TC"
		)

		# stock up item
		stock_entry = make_stock_entry(
			item_code=item_code, target="_Test Warehouse - _TC", qty=2, rate=100
		)

		# check if stock details are fetched and item is in stock with warehouse set
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertTrue(bool(data.product_info["in_stock"]))
		self.assertEqual(data.product_info["stock_qty"], 2)

		# unset warehouse
		frappe.db.set_value("Website Item", {"item_code": item_code}, "website_warehouse", "")

		# check if stock details are fetched and item not in stock without warehouse set
		# (even though it has stock in some warehouse)
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)
		self.assertFalse(bool(data.product_info["in_stock"]))
		self.assertFalse(bool(data.product_info["stock_qty"]))

		# disable show stock availability
		setup_webshop_settings({"show_stock_availability": 0})
		frappe.local.shopping_cart_settings = None
		data = get_product_info_for_website(item_code, skip_quotation_creation=True)

		# check if stock detail attributes are not fetched if stock availability is hidden
		self.assertIsNone(data.product_info.get("in_stock"))
		self.assertIsNone(data.product_info.get("stock_qty"))
		self.assertIsNone(data.product_info.get("show_stock_qty"))

		# tear down
		stock_entry.cancel()
		frappe.get_cached_doc("Website Item", {"item_code": "Test Mobile Phone"}).delete()

	def test_recommended_item(self):
		"Check if added recommended items are fetched correctly."
		item_code = "Test Mobile Phone"
		web_item = create_regular_web_item(item_code)

		setup_webshop_settings({"enable_recommendations": 1, "show_price": 1})

		# create recommended web item and price for it
		recommended_web_item = create_regular_web_item("Test Mobile Phone 1")
		make_web_item_price(item_code="Test Mobile Phone 1")

		# add recommended item to first web item
		web_item.append("recommended_items", {"website_item": recommended_web_item.name})
		web_item.save()

		frappe.local.shopping_cart_settings = None
		webshop_settings = get_shopping_cart_settings()
		recommended_items = web_item.get_recommended_items(webshop_settings)

		# test results if show price is enabled
		self.assertEqual(len(recommended_items), 1)
		recomm_item = recommended_items[0]
		self.assertEqual(recomm_item.get("website_item_name"), "Test Mobile Phone 1")
		self.assertTrue(bool(recomm_item.get("price_info")))  # price fetched

		price_info = recomm_item.get("price_info")
		self.assertEqual(price_info.get("price_list_rate"), 1000)
		self.assertEqual(price_info.get("formatted_price"), "₹ 1,000.00")

		# test results if show price is disabled
		setup_webshop_settings({"show_price": 0})

		frappe.local.shopping_cart_settings = None
		webshop_settings = get_shopping_cart_settings()
		recommended_items = web_item.get_recommended_items(webshop_settings)

		self.assertEqual(len(recommended_items), 1)
		self.assertFalse(bool(recommended_items[0].get("price_info")))  # price not fetched

		# tear down
		web_item.delete()
		recommended_web_item.delete()
		frappe.get_cached_doc("Item", "Test Mobile Phone 1").delete()

	def test_recommended_item_for_guest_user(self):
		"Check if added recommended items are fetched correctly for guest user."
		item_code = "Test Mobile Phone"
		web_item = create_regular_web_item(item_code)

		# price visible to guests
		setup_webshop_settings(
			{"enable_recommendations": 1, "show_price": 1, "hide_price_for_guest": 0}
		)

		# create recommended web item and price for it
		recommended_web_item = create_regular_web_item("Test Mobile Phone 1")
		make_web_item_price(item_code="Test Mobile Phone 1")

		# add recommended item to first web item
		web_item.append("recommended_items", {"website_item": recommended_web_item.name})
		web_item.save()

		frappe.set_user("Guest")

		frappe.local.shopping_cart_settings = None
		webshop_settings = get_shopping_cart_settings()
		recommended_items = web_item.get_recommended_items(webshop_settings)

		# test results if show price is enabled
		self.assertEqual(len(recommended_items), 1)
		self.assertTrue(bool(recommended_items[0].get("price_info")))  # price fetched

		# price hidden from guests
		frappe.set_user("Administrator")
		setup_webshop_settings({"hide_price_for_guest": 1})
		frappe.set_user("Guest")

		frappe.local.shopping_cart_settings = None
		webshop_settings = get_shopping_cart_settings()
		recommended_items = web_item.get_recommended_items(webshop_settings)

		# test results if show price is enabled
		self.assertEqual(len(recommended_items), 1)
		self.assertFalse(bool(recommended_items[0].get("price_info")))  # price fetched

		# tear down
		frappe.set_user("Administrator")
		web_item.delete()
		recommended_web_item.delete()
		frappe.get_cached_doc("Item", "Test Mobile Phone 1").delete()


def create_regular_web_item(item_code=None, item_args=None, web_args=None):
	"Create Regular Item and Website Item."
	item_code = item_code or "Test Mobile Phone"
	item = make_item(item_code, properties=item_args)

	if not frappe.db.exists("Website Item", {"item_code": item_code}):
		web_item = make_website_item(item, save=False)
		if web_args:
			web_item.update(web_args)
		web_item.save()
	else:
		web_item = frappe.get_cached_doc("Website Item", {"item_code": item_code})

	return web_item


def make_web_item_price(**kwargs):
	item_code = kwargs.get("item_code")
	if not item_code:
		return

	if not frappe.db.exists("Item Price", {"item_code": item_code}):
		item_price = frappe.get_doc(
			{
				"doctype": "Item Price",
				"item_code": item_code,
				"price_list": kwargs.get("price_list") or "_Test Price List India",
				"price_list_rate": kwargs.get("price_list_rate") or 1000,
			}
		)
		item_price.insert()
	else:
		item_price = frappe.get_cached_doc("Item Price", {"item_code": item_code})

	return item_price


def make_web_pricing_rule(**kwargs):
	title = kwargs.get("title")
	if not title:
		return

	if not frappe.db.exists("Pricing Rule", title):
		pricing_rule = frappe.get_doc(
			{
				"doctype": "Pricing Rule",
				"title": title,
				"apply_on": kwargs.get("apply_on") or "Item Code",
				"items": [{"item_code": kwargs.get("item_code")}],
				"selling": kwargs.get("selling") or 0,
				"buying": kwargs.get("buying") or 0,
				"rate_or_discount": kwargs.get("rate_or_discount") or "Discount Percentage",
				"discount_percentage": kwargs.get("discount_percentage") or 10,
				"company": kwargs.get("company") or "_Test Company",
				"currency": kwargs.get("currency") or "INR",
				"for_price_list": kwargs.get("price_list") or "_Test Price List India",
				"applicable_for": kwargs.get("applicable_for") or "",
				"customer": kwargs.get("customer") or "",
			}
		)
		pricing_rule.insert()
	else:
		pricing_rule = frappe.get_doc("Pricing Rule", {"title": title})

	return pricing_rule


def create_user_and_customer_if_not_exists(email, first_name=None):
	if frappe.db.exists("User", email):
		return

	frappe.get_doc(
		{
			"doctype": "User",
			"user_type": "Website User",
			"email": email,
			"send_welcome_email": 0,
			"first_name": first_name or email.split("@")[0],
		}
	).insert(ignore_permissions=True)

	contact = frappe.get_last_doc("Contact", filters={"email_id": email})
	link = contact.append("links", {})
	link.link_doctype = "Customer"
	link.link_name = "_Test Customer"
	link.link_title = "_Test Customer"
	contact.save()


test_dependencies = ["Price List", "Item Price", "Customer", "Contact", "Item"]
