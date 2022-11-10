import frappe


def execute():
    qb = frappe.qb
    table = frappe.qb.Table("tabSingles")
    old_doctype = "E Commerce Settings"
    new_doctype = "Webshop Settings"
    fields = ["doctype", "field", "value"]

    entries = qb.from_(table).select(*fields).where(table.doctype == old_doctype).run()

    for e in entries:
        qb.from_(table).insert(new_doctype, e.field, e.value).run()
