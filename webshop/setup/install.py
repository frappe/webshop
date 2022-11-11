import frappe


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


def after_install():
    copy_from_ecommerce_settings()
    drop_ecommerce_settings()
    remove_ecommerce_settings_doctype()
