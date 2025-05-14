import click
import frappe

from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from webshop.webshop.utils.setup import has_ecommerce_fields

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
	custom_fields = {
		"Item": [
			{
				"default": 0,
				"depends_on": "published_in_website",
				"fieldname": "published_in_website",
				"fieldtype": "Check",
				"ignore_user_permissions": 1,
				"insert_after": "default_manufacturer_part_no",
				"label": "Published In Website",
				"read_only": 1,
				"no_copy": 1,
			}
		],
		"Item Group": [
			{
				"fieldname": "custom_website_settings",
				"fieldtype": "Section Break",
				"label": "Website Settings",
				"insert_after": "taxes",
			},
			{
				"default": "0",
				"description": "Make Item Group visible in website",
				"fieldname": "show_in_website",
				"fieldtype": "Check",
				"label": "Show in Website",
				"insert_after": "custom_website_settings",
			},
			{
				"depends_on": "show_in_website",
				"fieldname": "route",
				"fieldtype": "Data",
				"label": "Route",
				"no_copy": 1,
				"unique": 1,
				"insert_after": "show_in_website",
			},
			{
				"depends_on": "show_in_website",
				"fieldname": "website_title",
				"fieldtype": "Data",
				"label": "Title",
				"insert_after": "route",
			},
			{
				"depends_on": "show_in_website",
				"description": "HTML / Banner that will show on the top of product list.",
				"fieldname": "description",
				"fieldtype": "Text Editor",
				"label": "Description",
				"insert_after": "website_title",
			},
			{
				"default": "0",
				"depends_on": "show_in_website",
				"description": "Include Website Items belonging to child Item Groups",
				"fieldname": "include_descendants",
				"fieldtype": "Check",
				"label": "Include Descendants",
				"insert_after": "website_title",
			},
			{
				"fieldname": "column_break_16",
				"fieldtype": "Column Break",
				"insert_after": "include_descendants",
			},
			{
				"depends_on": "show_in_website",
				"fieldname": "weightage",
				"fieldtype": "Int",
				"label": "Weightage",
				"insert_after": "column_break_16",
			},
			{
				"depends_on": "show_in_website",
				"description": "Show this slideshow at the top of the page",
				"fieldname": "slideshow",
				"fieldtype": "Link",
				"label": "Slideshow",
				"options": "Website Slideshow",
				"insert_after": "weightage",
			},
			{
				"depends_on": "show_in_website",
				"fieldname": "website_specifications",
				"fieldtype": "Table",
				"label": "Website Specifications",
				"options": "Item Website Specification",
				"insert_after": "description",
			},
			{
				"collapsible": 1,
				"depends_on": "show_in_website",
				"fieldname": "website_filters_section",
				"fieldtype": "Section Break",
				"label": "Website Filters",
				"insert_after": "website_specifications",
			},
			{
				"fieldname": "filter_fields",
				"fieldtype": "Table",
				"label": "Item Fields",
				"options": "Website Filter Field",
				"insert_after": "website_filters_section",
			},
			{
				"fieldname": "filter_attributes",
				"fieldtype": "Table",
				"label": "Attributes",
				"options": "Website Attribute",
				"insert_after": "filter_fields",
			},
		]
	}

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


