import frappe
import json
from webshop.api.search import product_search
from webshop.api import get_webshop_settings


def get_context(context):
	# query = frappe.form_dict.get("query") or ""
	query = frappe.form_dict.get("query") or frappe.form_dict.get("q") or ""

	context.query = query
	context.products = []
	context.webshop_settings = get_webshop_settings()

	if query:
		context.products = product_search(query)

	# تمرير المنتجات كـ JSON إلى JavaScript مع حماية
	context.products_json = json.dumps(context.products or [], default=str)
	context.webshop_settings_json = json.dumps(context.webshop_settings or {}, default=str)

	return context

