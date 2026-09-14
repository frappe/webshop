import frappe
import click

from webshop.webshop.utils.setup import get_custom_fields

def delete_custom_fields(custom_fields: dict):
	for doctype, fields in custom_fields.items():
		frappe.db.delete(
			"Custom Field",
			{
				"fieldname": ("in", [field["fieldname"] for field in fields]),
				"dt": doctype,
			},
		)

		frappe.clear_cache(doctype=doctype)

def before_uninstall():
    try:
        print("Removing customizations created by the Frappe Webshop...")
        delete_custom_fields(get_custom_fields())
    except Exception as e:
        BUG_REPORT_URL = "https://github.com/frappe/webshop/issues/new"
        click.secho(
			"Removing Customizations for Frappe Webshop failed due to an error."
			" Please try again or"
			f" report the issue on {BUG_REPORT_URL} if not resolved.",
			fg="bright_red",
		)
        raise e
    
    click.secho("Frappe Webshop customizations have been removed successfully...", fg="green")