// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Website Item', {
	onload: (frm) => {
		let images_button = $(".btn-attach[data-fieldname='website_images']");
		images_button.html("Upload Images");
		images_button.css("visibility", "hidden");

		frm.set_df_property("description", "read_only", 0);
		// should never check Private
		frm.fields_dict["website_image"].df.is_private = 0;

		if (frm.doc.custom_on_sale && frm.doc.custom_sales_price > 0)
			frm.set_value("custom_sale_price", frm.doc.custom_sales_price, 0, 1);
	},
	onload_post_render: (frm) => {
		setTimeout(function (frm) {
			console.log("loaded")
			let images_button = $(".btn-attach[data-fieldname='website_images']");
			images_button.css("visibility", "visible");
			$("div[data-fieldname='website_images']").find(".row").after(images_button);
		}, 1200);
	},
	custom_price: function (frm) {
		update_sale_price(frm)
	},
	custom_select_discount_type_: function (frm) {
		update_sale_price(frm)
	},
	custom_sales_price: function (frm) {
		reverse_update_sale_price(frm)
	},
	custom_set_discount_value: function (frm) {
		update_sale_price(frm)
	},
	custom_get_information_from_main_item(frm) {
		if (frm.doc.item_code == null) {
			frappe.msgprint("Please add item code to proceed");
		}
		frappe.call({
			freeze: true,
			freeze_message: "Loading item data...",
			method: 'webshop.webshop.doctype.website_item.custom_website_item.get_item_data_for_web_item',
			args: {
				'reference': frm.doc.name,
				'item_name': frm.doc.item_code,
			},
			callback: function (r) {
				response = r.message;
				frm.set_value("short_description", response.custom_short_description);
				frm.set_value("web_long_description", response.description);
				frm.set_value("custom_return__refund_title", response.custom_return__refund_title);
				frm.set_value("custom_long_description", response.custom_return__refund_description);
				frm.set_value("custom_shipping_title", response.custom_shipping_title);
				frm.set_value("custom_shipping_description", response.custom_shipping_description);
			}
		});
	},
	custom_get_images_from_main_item(frm) {
		if (frm.doc.item_code == null) {
			frappe.msgprint("Please add item code to proceed");
		} else {
			fetch_images(frm)
		}
	},
	refresh: (frm) => {
		frm.add_custom_button(__("Prices"), function () {
			frappe.set_route("List", "Item Price", { "item_code": frm.doc.item_code });
		}, __("View"));

		frm.add_custom_button(__("Stock"), function () {
			frappe.route_options = {
				"item_code": frm.doc.item_code
			};
			frappe.set_route("query-report", "Stock Balance");
		}, __("View"));

		frm.add_custom_button(__("Webshop Settings"), function () {
			frappe.set_route("Form", "Webshop Settings");
		}, __("View"));
	},

	copy_from_item_group: (frm) => {
		return frm.call({
			doc: frm.doc,
			method: "copy_specification_from_item_group"
		});
	},

	set_meta_tags: (frm) => {
		frappe.utils.set_meta_tag(frm.doc.route);
	}
});
function fetch_images(frm) {
	frappe.call({
		freeze: true,
		freeze_message: "Fetching Images",
		method: 'webshop.webshop.doctype.website_item.custom_website_item.get_images_from_item',
		args: {
			'item_code': frm.doc.item_code,
			'website_item': frm.doc.name,
		},
		callback: function (r) {
			frm.reload_doc();
		}
	});
}
function update_sale_price(frm) {
	let sale_price = 0;
	if (frm.doc.custom_on_sale) {
		if (frm.doc.custom_set_discount_value < 0) {
			frappe.msgprint("Negative numbers are not allowed")
			frm.set_value("custom_set_discount_value", 0);
			return;
		}
		if (frm.doc.custom_select_discount_type_ == "Discount Percentage") {
			if (frm.doc.custom_set_discount_value > 100) {
				frappe.msgprint("Discount percentage cannot be more than 100%")
				frm.set_value("custom_set_discount_value", 0);
				return;
			}
			sale_price = frm.doc.custom_set_discount_value / 100;
			sale_price = frm.doc.custom_price - (frm.doc.custom_price * sale_price);
		} else {
			if (frm.doc.custom_set_discount_value > frm.doc.custom_price) {
				frappe.msgprint("Sale price cannot be more than the product price")
				frm.set_value("custom_set_discount_value", 0);
				return;
			}
			sale_price = frm.doc.custom_price - frm.doc.custom_set_discount_value;
		}
		let discounted_value = Math.round((sale_price + Number.EPSILON) * 100) / 100;
		if (discounted_value < 1 || discounted_value == null || isNaN(discounted_value)) {
			discounted_value = 0;
		}
		discounted_value.toFixed(2)
		frm.set_value("custom_sale_price", discounted_value);
		$(".input-with-feedback[data-fieldname='custom_sales_price']").val(discounted_value);
		// frm.set_value("custom_sales_price", discounted_value );
		//frm.set_value("custom_sales_price", discounted_value );
	}
}
function reverse_update_sale_price(frm) {

	if (frm.doc.custom_sales_price > frm.doc.custom_price) {
		frappe.msgprint("Discount cannot be more than the product price")
		frm.set_value("custom_set_discount_value", 0);
		return;
	}

	let sale_price = 0;
	if (frm.doc.custom_on_sale) {
		discounted_value = frm.doc.custom_price - frm.doc.custom_sales_price;
		sale_price = frm.doc.custom_sales_price;
		if (frm.doc.custom_select_discount_type_ == "Discount Percentage") {
			frm.set_value("custom_select_discount_type_", "Discount Amount");
		}
		frm.set_value("custom_set_discount_value", discounted_value);
		// frm.set_value("custom_sales_price", sale_price );
	}
	$(".input-with-feedback[data-fieldname='custom_sales_price']").val($(".input-with-feedback[data-fieldname='custom_sales_price']").val());
	return;
}

