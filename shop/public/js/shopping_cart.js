// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// shopping cart
frappe.provide("shop.shop.shopping_cart");
var shopping_cart = shop.shop.shopping_cart;

var getParams = function (url) {
	var params = [];
	var parser = document.createElement('a');
	parser.href = url;
	var query = parser.search.substring(1);
	var vars = query.split('&');
	for (var i = 0; i < vars.length; i++) {
		var pair = vars[i].split('=');
		params[pair[0]] = decodeURIComponent(pair[1]);
	}
	return params;
};

frappe.ready(function () {
	var full_name = frappe.session && frappe.session.user_fullname;
	// update user
	if (full_name) {
		$('.navbar li[data-label="User"] a')
			.html('<i class="fa fa-fixed-width fa fa-user"></i> ' + full_name);
	}
	// set coupon code and sales partner code

	var url_args = getParams(window.location.href);

	var referral_coupon_code = url_args['cc'];
	var referral_sales_partner = url_args['sp'];

	var d = new Date();
	// expires within 30 minutes
	d.setTime(d.getTime() + (0.02 * 24 * 60 * 60 * 1000));
	var expires = "expires=" + d.toUTCString();
	if (referral_coupon_code) {
		document.cookie = "referral_coupon_code=" + referral_coupon_code + ";" + expires + ";path=/";
	}
	if (referral_sales_partner) {
		document.cookie = "referral_sales_partner=" + referral_sales_partner + ";" + expires + ";path=/";
	}
	referral_coupon_code = frappe.get_cookie("referral_coupon_code");
	referral_sales_partner = frappe.get_cookie("referral_sales_partner");

	if (referral_coupon_code && $(".tot_quotation_discount").val() == undefined) {
		$(".txtcoupon").val(referral_coupon_code);
	}
	if (referral_sales_partner) {
		$(".txtreferral_sales_partner").val(referral_sales_partner);
	}

	// update login
	shopping_cart.show_shoppingcart_dropdown();
	shopping_cart.set_cart_count();
	shopping_cart.show_cart_navbar();
});

$.extend(shopping_cart, {
	show_shoppingcart_dropdown: function () {
		$(".shopping-cart").on('shown.bs.dropdown', function () {
			if (!$('.shopping-cart-menu .cart-container').length) {
				return frappe.call({
					method: 'shop.shop.shopping_cart.cart.get_shopping_cart_menu',
					callback: function (r) {
						if (r.message) {
							$('.shopping-cart-menu').html(r.message);
						}
					}
				});
			}
		});
	},

	update_cart: function (opts) {
		shopping_cart.get_settings().then((settings) => {
			shopping_cart.freeze();
			return frappe.call({
				type: "POST",
				method: "shop.shop.shopping_cart.cart.update_cart",
				args: {
					item_code: opts.item_code,
					qty: opts.qty,
					additional_notes: opts.additional_notes !== undefined ? opts.additional_notes : undefined,
					with_items: opts.with_items || 0
				},
				btn: opts.btn,
				callback: function (r) {
					shopping_cart.unfreeze();
					shopping_cart.set_cart_count(true);
					if (opts.callback)
						opts.callback(r);
				}
			});
		});
	},

	set_cart_count: function (animate = false) {
		$(".intermediate-empty-cart").remove();

		var cart_count = frappe.get_cookie("cart_count");
		shopping_cart.get_settings().then((settings) => {
			if (frappe.session.user === "Guest" && settings && settings.allow_guest_checkout === 0) {
				cart_count = 0;
			}

			if (cart_count) {
				$(".shopping-cart").toggleClass('hidden', false);
			}

			var $cart = $('.cart-icon');
			var $badge = $cart.find("#cart-count");

			if (parseInt(cart_count) === 0 || cart_count === undefined) {
				$cart.css("display", "none");
				$(".cart-tax-items").hide();
				$(".btn-place-order").hide();
				$(".cart-payment-addresses").hide();

				let intermediate_empty_cart_msg = `
					<div class="text-center w-100 intermediate-empty-cart mt-4 mb-4 text-muted">
						${__("Cart is Empty")}
					</div>
				`;
				if (!$(".intermediate-empty-cart").length) {
					$(".cart-table").after(intermediate_empty_cart_msg);
				}
			}
			else {
				$cart.css("display", "inline");
				$("#cart-count").text(cart_count);

				if ($badge.length) {
					$badge.html(cart_count);
				} else {
					$cart.append(`<span class="badge" id="cart-count">${cart_count}</span>`);
				}

				if (animate) {
					$cart.addClass("cart-animate");
					setTimeout(() => {
						$cart.removeClass("cart-animate");
					}, 500);
				}
			}
		});
	},

	shopping_cart_update: function ({ item_code, qty, cart_dropdown, additional_notes }) {
		shopping_cart.update_cart({
			item_code,
			qty,
			additional_notes,
			with_items: 1,
			btn: this,
			callback: function (r) {
				if (!r.exc) {
					$(".cart-items").html(r.message.items);
					$(".cart-tax-items").html(r.message.total);
					$(".payment-summary").html(r.message.taxes_and_totals);
					shopping_cart.set_cart_count();

					if (cart_dropdown != true) {
						$(".cart-icon").hide();
					}
				}
			},
		});
	},

	show_cart_navbar: function () {
		shopping_cart.get_settings().then((settings) => {
			$(".shopping-cart").toggleClass('hidden', settings.enabled ? false : true);
		});
	},

	get_settings: function () {
		if (shopping_cart.settings) {
			return Promise.resolve(shopping_cart.settings);
		}
		return frappe.call({
			method: "shop.shop.doctype.shop_settings.shop_settings.get_cart_settings",
			callback: function (r) {
				shopping_cart.settings = r.message;
			}
		}).then((r) => r.message);
	},

	toggle_button_class(button, remove, add) {
		button.removeClass(remove);
		button.addClass(add);
	},

	bind_add_to_cart_action() {
		$('.page_content').on('click', '.btn-add-to-cart-list', (e) => {
			const $btn = $(e.currentTarget);
			$btn.prop('disabled', true);

			shopping_cart.add_to_cart_execution($btn);

			shopping_cart.add_to_cart_execution($btn);
		});
	},

	add_to_cart_execution: function ($btn) {
		$btn.addClass('hidden');
		$btn.closest('.cart-action-container').addClass('d-flex');
		$btn.parent().find('.go-to-cart').removeClass('hidden');
		$btn.parent().find('.go-to-cart-grid').removeClass('hidden');
		$btn.parent().find('.cart-indicator').removeClass('hidden');

		const item_code = $btn.data('item-code');
		shop.shop.shopping_cart.update_cart({
			item_code,
			qty: 1
		});
	},

	freeze() {
		if (window.location.pathname !== "/cart") return;

		if (!$('#freeze').length) {
			let freeze = $('<div id="freeze" class="modal-backdrop fade"></div>')
				.appendTo("body");

			setTimeout(function () {
				freeze.addClass("show");
			}, 1);
		} else {
			$("#freeze").addClass("show");
		}
	},

	unfreeze() {
		if ($('#freeze').length) {
			let freeze = $('#freeze').removeClass("show");
			setTimeout(function () {
				freeze.remove();
			}, 1);
		}
	}
});
