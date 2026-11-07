import frappe


def execute():
	# the field is gone from the doctype by now, but its value is still stored
	old_account = frappe.db.get_singles_dict("Webshop Settings").get("payment_gateway_account")
	if not old_account:
		return

	# select everything because the parent column may not exist until the payments patch runs
	row = frappe.db.get_value("Payment Gateway Account", old_account, "*", as_dict=True)
	if not row:
		return

	frappe.db.set_single_value(
		"Webshop Settings",
		{
			"payment_gateway": row.get("parent") or row.get("payment_gateway"),
			"payment_account": row.payment_account,
		},
		update_modified=False,
	)
