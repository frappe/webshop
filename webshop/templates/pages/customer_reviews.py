# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe

from webshop.webshop.doctype.webshop_settings.webshop_settings import (
	get_shopping_cart_settings,
)
from webshop.webshop.doctype.item_review.item_review import get_item_reviews
from webshop.webshop.doctype.website_item.website_item import check_if_user_is_customer


def get_context(context):
	context.body_class = "product-page"
	context.no_cache = 1
	context.full_page = True
	context.reviews = None

	if frappe.form_dict and frappe.form_dict.get("web_item"):
		context.web_item = frappe.form_dict.get("web_item")
		context.user_is_customer = check_if_user_is_customer()
		context.enable_reviews = get_shopping_cart_settings().enable_reviews

		if context.enable_reviews:
			reviews_data = get_item_reviews(context.web_item)
			context.update(reviews_data)
