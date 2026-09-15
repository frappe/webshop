import frappe
import frappe.defaults


def before_tests():
	from erpnext.setup.utils import before_tests as erpnext_before_tests

	erpnext_before_tests()

	# erpnext points the default Customer Group at the root node, which is a group.
	# The cart creates Customers without a group of their own, so `Document._set_defaults`
	# fills in that root and `Customer.validate_customer_group` rejects it.
	frappe.defaults.clear_default("customer_group")
	frappe.db.commit()  # nosemgrep
