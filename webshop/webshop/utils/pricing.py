# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import annotations

import frappe
from frappe.utils import cint, flt, fmt_money

from erpnext.accounts.doctype.pricing_rule.pricing_rule import get_pricing_rule_for_item


def get_price_for_store(
	item_code: str,
	price_list: str,
	warehouse: str | None,
	company: str,
	customer_group: str,
	party=None,
	qty: float = 1,
):
	"""Store-aware wrapper around `erpnext.utilities.product.get_price`.

	Ensures warehouse-aware Pricing Rules are evaluated by passing the active store's warehouse.
	"""

	template_item_code = frappe.db.get_value("Item", item_code, "variant_of")

	if not price_list:
		return {}

	price = _get_price_list_rate(item_code, price_list)

	if template_item_code and not price:
		price = _get_price_list_rate(template_item_code, price_list)

	if not price:
		return {}

	pricing_rule_dict = frappe._dict(
		{
			"item_code": item_code,
			"qty": qty,
			"stock_qty": qty,
			"transaction_type": "selling",
			"price_list": price_list,
			"customer_group": customer_group,
			"company": company,
			"conversion_rate": 1,
			"for_shopping_cart": True,
			"currency": frappe.db.get_value("Price List", price_list, "currency"),
			"doctype": "Quotation",
			"warehouse": warehouse,
		}
	)

	if party and getattr(party, "doctype", None) == "Customer":
		pricing_rule_dict.update({"customer": party.name})

	price_obj = _apply_pricing_rules(price[0], pricing_rule_dict)

	if not price_obj:
		return {}

	return _format_price_details(item_code, price_obj)


def _get_price_list_rate(item_code: str, price_list: str):
	return frappe.get_all(
		"Item Price",
		fields=["price_list_rate", "currency"],
		filters={"price_list": price_list, "item_code": item_code},
	)


def _apply_pricing_rules(price_obj, pricing_rule_dict):
	pricing_rule = get_pricing_rule_for_item(pricing_rule_dict)

	if not pricing_rule:
		return price_obj

	mrp = price_obj.price_list_rate or 0

	if pricing_rule.pricing_rule_for == "Discount Percentage":
		price_obj.discount_percent = pricing_rule.discount_percentage
		price_obj.formatted_discount_percent = f"{flt(pricing_rule.discount_percentage, 0)}%"
		price_obj.price_list_rate = flt(
			price_obj.price_list_rate
			* (1.0 - (flt(pricing_rule.discount_percentage) / 100.0))
		)

	if pricing_rule.pricing_rule_for == "Rate":
		rate_discount = flt(mrp) - flt(pricing_rule.price_list_rate)
		if rate_discount > 0:
			price_obj.formatted_discount_rate = fmt_money(
				rate_discount, currency=price_obj["currency"]
			)
		price_obj.price_list_rate = pricing_rule.price_list_rate or 0

	price_obj._mrp = mrp
	return price_obj


def _format_price_details(item_code: str, price_obj):
	mrp = getattr(price_obj, "_mrp", price_obj.price_list_rate or 0)

	price_obj["formatted_price"] = fmt_money(
		price_obj["price_list_rate"], currency=price_obj["currency"]
	)
	if mrp != price_obj["price_list_rate"]:
		price_obj["formatted_mrp"] = fmt_money(mrp, currency=price_obj["currency"])

	price_obj["currency_symbol"] = (
		not cint(frappe.db.get_default("hide_currency_symbol"))
		and (
			frappe.db.get_value("Currency", price_obj.currency, "symbol", cache=True)
			or price_obj.currency
		)
		or ""
	)

	uom_conversion_factor = frappe.db.sql(
		"""select C.conversion_factor
		from `tabUOM Conversion Detail` C
		inner join `tabItem` I on C.parent = I.name and C.uom = I.sales_uom
		where I.name = %s""",
		item_code,
	)

	uom_conversion_factor = uom_conversion_factor[0][0] if uom_conversion_factor else 1
	price_obj["formatted_price_sales_uom"] = fmt_money(
		price_obj["price_list_rate"] * uom_conversion_factor,
		currency=price_obj["currency"],
	)

	if not price_obj["price_list_rate"]:
		price_obj["price_list_rate"] = 0

	if not price_obj["currency"]:
		price_obj["currency"] = ""

	if not price_obj.get("formatted_price"):
		price_obj["formatted_price"] = ""
		price_obj["formatted_mrp"] = ""

	# remove helper attribute
	if hasattr(price_obj, "_mrp"):
		delattr(price_obj, "_mrp")

	return price_obj
