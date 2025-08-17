// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Webshop Homepage", {
    refresh(frm) {
        console.log("Website Item Group form refreshed");
        frm.set_query("item_group", "homepage_collections", () => {
            return {
                filters: {
                    parent_item_group: "Webshop",
                },
            };
        });
    },
});

frappe.ui.form.on("Website Item Group", {
    onload(frm){
        console.log("Website Item Groupie form loaded");
    }
});
