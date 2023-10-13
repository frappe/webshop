# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
import unittest

import frappe
from frappe.core.doctype.user_permission.test_user_permission import create_user

from webshop.webshop.doctype.webshop_settings.test_webshop_settings import (
	setup_webshop_settings,
)
from webshop.webshop.doctype.item_review.item_review import (
	UnverifiedReviewer,
	add_item_review,
	get_item_reviews,
)
from webshop.webshop.doctype.website_item.website_item import make_website_item
from webshop.webshop.shopping_cart.cart import get_party
from erpnext.stock.doctype.item.test_item import make_item


class TestItemReview(unittest.TestCase):
	def setUp(self):
		item = make_item("Test Mobile Phone")
		if not frappe.db.exists("Website Item", {"item_code": "Test Mobile Phone"}):
			make_website_item(item, save=True)

		frappe.set_user("Administrator")
		setup_webshop_settings({"enable_reviews": 1, "enabled": 1})
		frappe.local.shopping_cart_settings = None

	def tearDown(self):
		frappe.set_user("Administrator")

		website_item_doc = frappe.get_cached_doc("Website Item", {"item_code": "Test Mobile Phone"})
		reviews = frappe.get_all("Item Review", {"website_item": website_item_doc.name})
		for review in reviews:
			frappe.delete_doc("Item Review", review.name)

		website_item_doc.delete()
		setup_webshop_settings({"enable_reviews": 0})

	def test_add_and_get_item_reviews_from_customer(self):
		"Add / Get Reviews from a User that is a valid customer (has added to cart or purchased in the past)"
		# create user
		web_item = frappe.db.get_value("Website Item", {"item_code": "Test Mobile Phone"})
		test_user = create_user("test_reviewer@example.com", "Customer")
		frappe.set_user(test_user.name)

		# create customer and contact against user
		customer = get_party()

		# post review on "Test Mobile Phone"
		try:
			add_item_review(web_item, "Great Product", 3, "Would recommend this product")
			review_name = frappe.db.get_value("Item Review", {"website_item": web_item})
		except Exception:
			self.fail(f"Error while publishing review for {web_item}")

		review_data = get_item_reviews(web_item, 0, 10)

		self.assertEqual(len(review_data.reviews), 1)
		self.assertTrue(review_data.average_rating)
		self.assertEqual(review_data.reviews_per_rating[0], 100)

		# tear down
		frappe.set_user("Administrator")
		frappe.delete_doc("Item Review", review_name)
		customer.delete()

	def test_add_item_review_from_non_customer(self):
		"Check if logged in user (who is not a customer yet) is blocked from posting reviews."
		web_item = frappe.db.get_value("Website Item", {"item_code": "Test Mobile Phone"})
		test_user = create_user("test_reviewer@example.com", "Customer")
		frappe.set_user(test_user.name)

		with self.assertRaises(UnverifiedReviewer):
			add_item_review(web_item, "Great Product", 3, "Would recommend this product")

		# tear down
		frappe.set_user("Administrator")

	def test_add_item_reviews_from_guest_user(self):
		"Check if Guest user is blocked from posting reviews."
		web_item = frappe.db.get_value("Website Item", {"item_code": "Test Mobile Phone"})
		frappe.set_user("Guest")

		with self.assertRaises(UnverifiedReviewer):
			add_item_review(web_item, "Great Product", 3, "Would recommend this product")

		# tear down
		frappe.set_user("Administrator")
