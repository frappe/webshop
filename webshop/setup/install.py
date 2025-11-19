import click
import frappe

from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from webshop.webshop.utils.setup import has_ecommerce_fields, get_custom_fields

def after_install():
	run_patches()
	copy_from_ecommerce_settings()
	drop_ecommerce_settings()
	remove_ecommerce_settings_doctype()
	add_custom_fields()
	navbar_add_products_link()
	say_thanks()


def copy_from_ecommerce_settings():
	if not has_ecommerce_fields():
		return

	frappe.reload_doc("webshop", "doctype", "webshop_settings")

	qb = frappe.qb
	table = frappe.qb.Table("tabSingles")
	old_doctype = "E Commerce Settings"
	new_doctype = "Webshop Settings"

	entries = (
		qb.from_(table)
		.select(table.field, table.value)
		.where((table.doctype == old_doctype) & (table.field != "name"))
		.run(as_dict=True)
	)

	for e in entries:
		qb.into(table).insert(new_doctype, e.field, e.value).run()

	for doctype in ["Website Filter Field", "Website Attribute"]:
		table = qb.DocType(doctype)
		query = (
			qb.update(table)
			.set(table.parent, new_doctype)
			.set(table.parenttype, new_doctype)
			.where(table.parent == old_doctype)
		)

		query.run()

def drop_ecommerce_settings():
	frappe.delete_doc_if_exists("DocType", "E Commerce Settings", force=True)


def remove_ecommerce_settings_doctype():
	if not has_ecommerce_fields():
		return

	table = frappe.qb.Table("tabSingles")
	old_doctype = "E Commerce Settings"

	frappe.qb.from_(table).delete().where(table.doctype == old_doctype).run()


def add_custom_fields():
	custom_fields = get_custom_fields()

	frappe.make_property_setter(
		{
			"doctype": "Item Group",
			"doctype_or_field": "DocType",
			"fieldname": "allow_guest_to_view",
			"property": "allow_guest_to_view",
			"value": 1,
			"property_type": "Check"
		},
		is_system_generated=True,
	)

	return create_custom_fields(custom_fields)

def navbar_add_products_link():
	website_settings = frappe.get_doc("Website Settings")
	if website_settings.top_bar_items:
		return

	website_settings.append(
		"top_bar_items",
		{
			"label": _("Products"),
			"url": "/all-products",
			"right": False,
		},
	)

	website_settings.save()


def say_thanks():
	click.secho("Thank you for installing Frappe Webshop!", color="green")


patches = [
	"create_website_items",
	"populate_e_commerce_settings",
	"add_homepage_field",
	"make_homepage_products_website_items",
	"fetch_thumbnail_in_website_items",
	"convert_to_website_item_in_item_card_group_template",
	"shopping_cart_to_ecommerce",
	"copy_custom_field_filters_to_website_item",
]

def run_patches():
	# Customers migrating from v13 to v15 directly need to run all below patches

	frappe.flags.in_patch = True

	try:
		for patch in patches:
			frappe.get_attr(f"webshop.patches.{patch}.execute")()

	finally:
		frappe.flags.in_patch = False


