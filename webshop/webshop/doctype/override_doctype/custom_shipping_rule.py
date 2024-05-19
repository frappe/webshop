#BDivecha
import frappe
from frappe.utils import flt
from erpnext.accounts.doctype.shipping_rule.shipping_rule import (
    ShippingRule
)


class CustomShippingRule(ShippingRule):
	def apply(self, doc):
		shipping_amount = 0.0
		by_value = False
		
		from_address = None
		to_address = None

		if self.custom_location_based:
			if len(doc.get('items')) > 0:
				first_item = doc.get('items')[0].item_code
			else:
				first_item = None

			warehouse = frappe.get_cached_value("Website Item", {"item_code": first_item}, "website_warehouse")
			from_address = frappe.db.get_value("Warehouse", warehouse, "custom_region")
			to_address = doc.get_shipping_address().custom_region
		
		if doc.get_shipping_address():
			# validate country only if there is address
			self.validate_countries(doc)

		if self.calculate_based_on == "Net Total":
			value = doc.base_net_total
			by_value = True

		elif self.calculate_based_on == "Net Weight":
			value = doc.total_net_weight
			by_value = True

		elif self.calculate_based_on == "Fixed":
			shipping_amount = self.shipping_amount

		# shipping amount by value, apply conditions
		if by_value:
			shipping_amount = self.get_shipping_amount_from_rules(value, from_address, to_address)

		# convert to order currency
		if doc.currency != doc.company_currency:
			shipping_amount = flt(shipping_amount / doc.conversion_rate, 2)

		self.add_shipping_rule_to_tax_table(doc, shipping_amount)

	def get_shipping_amount_from_rules(self, value, from_address=None, to_address=None):
		if from_address and to_address:
			for condition in self.get("conditions"):
				if not condition.to_value or (flt(condition.from_value) <= flt(value) <= flt(condition.to_value) and condition.custom_from_region == from_address and condition.custom_to_region == to_address):
					return condition.shipping_amount
		else:
			for condition in self.get("conditions"):
				if not condition.to_value or (flt(condition.from_value) <= flt(value) <= flt(condition.to_value)):
					return condition.shipping_amount

		return 0.0