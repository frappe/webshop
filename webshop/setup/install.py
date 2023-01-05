import click
import frappe

from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def after_install():
    copy_from_ecommerce_settings()
    drop_ecommerce_settings()
    remove_ecommerce_settings_doctype()
    add_custom_fields()
    navbar_add_products_link()
    say_thanks()


def copy_from_ecommerce_settings():
    qb = frappe.qb
    table = frappe.qb.Table("tabSingles")
    old_doctype = "E Commerce Settings"
    new_doctype = "Webshop Settings"
    fields = ("field", "value")

    entries = (
        qb.from_(table)
        .select(*fields)
        .where(table.doctype == old_doctype)
        .run(as_dict=True)
    )

    for e in entries:
        qb.into(table).insert(new_doctype, e.field, e.value).run()


def drop_ecommerce_settings():
    frappe.delete_doc_if_exists("DocType", "E Commerce Settings", force=True)


def remove_ecommerce_settings_doctype():
    table = frappe.qb.Table("tabSingles")
    old_doctype = "E Commerce Settings"

    frappe.qb.from_(table).delete().where(table.doctype == old_doctype).run()


def add_custom_fields():
    d = {
        "Item": [
            {
                "fieldname": "published_in_website",
                "fieldtype": "Check",
                "ignore_user_permissions": 1,
                "label": "Published In Website",
            }
        ]
    }

    return create_custom_field(d)


def navbar_add_products_link():
    website_settings = frappe.get_single("Website Settings")

    if not website_settings:
        return

    website_settings.append(
        "top_bar_items",
        {
            "label": _("Products"),
            "url": "/all-products",
            "right": False,
        },
    )

    return website_settings.save()


def say_thanks():
    click.secho("Thank you for installing Frappe Webshop!", color="green")
