frappe.ui.form.on("Item", {
    refresh: function(frm) {
		if (!frm.doc.__islocal) {
			if (!frm.doc.published_in_website) {
				frm.add_custom_button(__("Publish in Website"), function() {
					frappe.call({
						method: "webshop.webshop.doctype.website_item.website_item.make_website_item",
						args: {
							doc: frm.doc,
						},
						freeze: true,
						freeze_message: __("Publishing Item ..."),
						callback: function(result) {
							frappe.msgprint({
								message: __("Website Item {0} has been created.",
									[repl('<a href="/app/website-item/%(item_encoded)s" class="strong">%(item)s</a>', {
										item_encoded: encodeURIComponent(result.message[0]),
										item: result.message[1]
									})]
								),
								title: __("Published"),
								indicator: "green"
							});
						}
					});
				}, __('Actions'));
			} else {
				frm.add_custom_button(__("View Website Item"), function() {
					frappe.db.get_value("Website Item", {item_code: frm.doc.name}, "name", (d) => {
						if (!d.name) frappe.throw(__("Website Item not found"));
						frappe.set_route("Form", "Website Item", d.name);
					});
				});
			}
		}
	}
});
