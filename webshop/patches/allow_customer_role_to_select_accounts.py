import frappe
from frappe.permissions import add_permission, update_permission_property


def execute():
	"""Let a shopper's cart resolve the receivable account behind their own Quotation.

	erpnext's `get_party_account` checks permission on the account it resolves, and
	`Quotation.validate` reaches it through `set_payment_schedule`. A storefront shopper holds the
	`Customer` role, which by design carries almost no permissions, so saving a cart raises
	"User don't have permissions to select/read this account."

	erpnext writes that check as `select if only_has_select_perm("Account") else read`, so `select`
	alone satisfies it. `select` lets a Link field resolve; it does not expose the account's data. That
	is the narrowest grant that makes the cart work, so it is the one this ships.
	"""
	if not frappe.db.exists("Role", "Customer"):
		return

	add_permission("Account", "Customer", 0)
	update_permission_property("Account", "Customer", 0, "select", 1)
	update_permission_property("Account", "Customer", 0, "read", 0)
