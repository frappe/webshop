// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Homepage", {
    refresh(frm) {
        frm.set_query("item_group", "homepage_collections", () => {
            return {
                filters: {
                    parent_item_group: [
                        "descendants of (inclusive)",
                        "Webshop",
                    ],
                },
            };
        });
    },
});
