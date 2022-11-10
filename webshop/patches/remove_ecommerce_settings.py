import frappe


def execute():
    table = frappe.qb.Table("tabSingles")
    old_doctype = "E Commerce Settings"

    frappe.qb.from_(table).delete().where(table.doctype == old_doctype).run()
