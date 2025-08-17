// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Website Item", {
    onload: (frm) => {
        // should never check Private
        frm.fields_dict["website_image"].df.is_private = 0;
    },

    refresh: (frm) => {
        frm.add_custom_button(
            __("Prices"),
            function () {
                frappe.set_route("List", "Item Price", {
                    item_code: frm.doc.item_code,
                });
            },
            __("View")
        );

        frm.add_custom_button(
            __("Stock"),
            function () {
                frappe.route_options = {
                    item_code: frm.doc.item_code,
                };
                frappe.set_route("query-report", "Stock Balance");
            },
            __("View")
        );

        frm.add_custom_button(
            __("Webshop Settings"),
            function () {
                frappe.set_route("Form", "Webshop Settings");
            },
            __("View")
        );
        
        new frappe.ui.custom.AssetViewer({
            wrapper: document.getElementById(
                "website-item-asset-management-ui-wrapper"
            ),
            frm: frm,
            item_code: frm.doc.item_code,
            web_item_code: frm.doc.name,
        });
        frm.set_query("website_item_groups_multiselect", () => {
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

    copy_from_item_group: (frm) => {
        return frm.call({
            doc: frm.doc,
            method: "copy_specification_from_item_group",
        });
    },

    set_meta_tags: (frm) => {
        frappe.utils.set_meta_tag(frm.doc.route);
    },

    item_code: (frm) => {
        frm.refresh();
    },
});
