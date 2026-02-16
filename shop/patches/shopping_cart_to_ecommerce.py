import click
import frappe


def execute():

	frappe.delete_doc("DocType", "Shopping Cart Settings", ignore_missing=True)
	frappe.delete_doc("DocType", "Products Settings", ignore_missing=True)
	frappe.delete_doc("DocType", "Supplier Item Group", ignore_missing=True)
