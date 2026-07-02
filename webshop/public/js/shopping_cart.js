// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// shopping cart
frappe.provide("webshop.webshop.shopping_cart");
var shopping_cart = webshop.webshop.shopping_cart;

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

frappe.ready(function() {
	var full_name = frappe.session && frappe.session.user_fullname;
	// update user
	if(full_name) {
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
	var expires = "expires="+d.toUTCString();
	if (referral_coupon_code) {
		document.cookie = "referral_coupon_code=" + referral_coupon_code + ";" + expires + ";path=/";
	}
	if (referral_sales_partner) {
		document.cookie = "referral_sales_partner=" + referral_sales_partner + ";" + expires + ";path=/";
	}
	referral_coupon_code=frappe.get_cookie("referral_coupon_code");
	referral_sales_partner=frappe.get_cookie("referral_sales_partner");

	if (referral_coupon_code && $(".tot_quotation_discount").val()==undefined ) {
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
	show_shoppingcart_dropdown: function() {
		$(".shopping-cart").on('shown.bs.dropdown', function() {
			if (!$('.shopping-cart-menu .cart-container').length) {
				return frappe.call({
					method: 'webshop.webshop.shopping_cart.cart.get_shopping_cart_menu',
					callback: function(r) {
						if (r.message) {
							$('.shopping-cart-menu').html(r.message);
						}
					}
				});
			}
		});
	},

	update_cart: function(opts) {
		if (frappe.session.user==="Guest") {
			// Save in local storage for persistence but don't redirect
			if (localStorage) {
				localStorage.setItem("last_visited", window.location.pathname);
			}
		} 
		
		shopping_cart.freeze();
		return frappe.call({
			type: "POST",
			method: "webshop.webshop.shopping_cart.cart.update_cart",
			args: {
				item_code: opts.item_code,
				qty: opts.qty,
				uom: opts.uom,
				additional_notes: opts.additional_notes !== undefined ? opts.additional_notes : undefined,
				with_items: opts.with_items || 0
			},
			btn: opts.btn,
			callback: function(r) {
				shopping_cart.unfreeze();
				shopping_cart.set_cart_count(true);
				if(opts.callback)
					opts.callback(r);
			}
		});
	},

	refresh_cart_icon(cart) {
		const $cart_icon = $('.shopping-cart-icon');
		const count = (cart && cart.items) ? cart.items.length : 0;
		$('.cart-count').text(count).toggleClass('hidden', count === 0);
		
		// Animate
		$cart_icon.addClass('cart-bump');
		setTimeout(() => $cart_icon.removeClass('cart-bump'), 400);
	},

	set_cart_count: function(animate=false) {
		$(".intermediate-empty-cart").remove();

		var cart_count = frappe.get_cookie("cart_count");

		if(cart_count) {
			$(".shopping-cart").toggleClass('hidden', false);
		}

		var $cart = $('.cart-icon');
		var $badge = $cart.find("#cart-count");

		if(parseInt(cart_count) === 0 || cart_count === undefined) {
			$cart.css("display", "none");
			$(".cart-tax-items").hide();
			$(".btn-place-order").hide();
			$(".cart-payment-addresses").hide();

			let intermediate_empty_cart_msg = `
				<div class="text-center w-100 intermediate-empty-cart mt-4 mb-4 text-muted">
					${ __("Cart is Empty") }
				</div>
			`;
			$(".cart-table").after(intermediate_empty_cart_msg);
		}
		else {
			$cart.css("display", "inline");
			$("#cart-count").text(cart_count);
		}

		if(cart_count) {
			$badge.html(cart_count);

			if (animate) {
				$cart.addClass("cart-animate");
				setTimeout(() => {
					$cart.removeClass("cart-animate");
				}, 500);
			}
		} else {
			$badge.remove();
		}
	},

	shopping_cart_update: function({item_code, qty, cart_dropdown, additional_notes}) {
		shopping_cart.update_cart({
			item_code,
			qty,
			additional_notes,
			with_items: 1,
			btn: this,
			callback: function(r) {
				if(!r.exc) {
					// Open and Update Drawer
					if (window.location.pathname !== "/cart") {
						if (!$("#cart-drawer").hasClass("open")) {
							shopping_cart.toggle_drawer();
						} else {
							shopping_cart.refresh_drawer_ui(r.message);
						}
					}
					
					$(".cart-items").html(r.message.items);
					$(".cart-tax-items").html(r.message.total);
					$(".payment-summary").html(r.message.taxes_and_totals);
					shopping_cart.set_cart_count();

					if (cart_dropdown != true && window.location.pathname === "/cart") {
						$(".cart-icon").hide();
					}
				}
			},
		});
	},

	show_cart_navbar: function () {
		frappe.call({
			method: "webshop.webshop.doctype.webshop_settings.webshop_settings.is_cart_enabled",
			callback: function(r) {
				$(".shopping-cart").toggleClass('hidden', r.message ? false : true);
			}
		});
	},

	toggle_button_class(button, remove, add) {
		button.removeClass(remove);
		button.addClass(add);
	},

	bind_add_to_cart_action() {
		$('.page_content').on('click', '.btn-add-to-cart-list', (e) => {
			const $btn = $(e.currentTarget);
			$btn.prop('disabled', true);

			$btn.addClass('hidden');
			$btn.closest('.cart-action-container').addClass('d-flex');
			$btn.parent().find('.go-to-cart').removeClass('hidden');
			$btn.parent().find('.go-to-cart-grid').removeClass('hidden');
			$btn.parent().find('.cart-indicator').removeClass('hidden');

			const item_code = $btn.data('item-code');
			shopping_cart.update_cart({
				item_code: item_code,
				qty: 1,
				callback: function(r) {
					$btn.prop('disabled', false);
					if (r.message && !r.exc) {
						if (shopping_cart.toggle_drawer) {
							shopping_cart.toggle_drawer();
						}
					}
				}
			});

		});
	},

	freeze() {
		if (window.location.pathname !== "/cart") return;

		if (!$('#freeze').length) {
			let freeze = $('<div id="freeze" class="modal-backdrop fade"></div>')
				.appendTo("body");

			setTimeout(function() {
				freeze.addClass("show");
			}, 1);
		} else {
			$("#freeze").addClass("show");
		}
	},

	unfreeze() {
		if ($('#freeze').length) {
			let freeze = $('#freeze').removeClass("show");
			setTimeout(function() {
				freeze.remove();
			}, 1);
		}
	},

	toggle_drawer: function() {
		const $drawer = $("#cart-drawer");
		const $backdrop = $("#cart-drawer-backdrop");
		
		if ($drawer.hasClass("open")) {
			$drawer.removeClass("open");
			$backdrop.removeClass("open");
		} else {
			$drawer.addClass("open");
			$backdrop.addClass("open");
			this.refresh_drawer();
		}
	},

	refresh_drawer: function() {
		const $items_container = $("#cart-drawer-items");
		const $summary_container = $("#cart-drawer-summary");
		
		frappe.call({
			method: "webshop.webshop.shopping_cart.cart.get_cart_drawer",
			callback: function(r) {
				if (r.message) {
					shopping_cart.refresh_drawer_ui(r.message);
				} else {
					shopping_cart.show_drawer_error();
				}
			},
			error: function() {
				shopping_cart.show_drawer_error();
			}
		});
	},

	show_drawer_error: function() {
		$("#cart-drawer-items").html(`
			<div class="text-center py-5 text-muted">
				<p class="small mb-3">Unable to load your cart right now.</p>
				<button class="btn btn-sm btn-primary" onclick="webshop.webshop.shopping_cart.refresh_drawer()">
					Retry
				</button>
			</div>
		`);
		$("#cart-drawer-summary").html("");
	},

	show_coupon_message: function(message, indicator="info") {
		const color_class = indicator === "success" ? "text-success" : indicator === "danger" ? "text-danger" : "text-muted";
		$("#cart-drawer-coupon-msg")
			.removeClass("text-success text-danger text-muted")
			.addClass(color_class)
			.text(message || "");
	},

	refresh_drawer_ui: function(message) {
		$("#cart-drawer-items").html(message.items || '<div class="text-center py-5 text-muted">No items in cart</div>');
		$("#cart-drawer-summary").html(message.taxes_and_totals || "");
		
		// Bind quantity buttons in drawer
		$("#cart-drawer-items .btn-qty").on('click', function() {
			const $btn = $(this);
			const item_code = $btn.data('item-code');
			const $input = $btn.siblings('.qty-input');
			let qty = parseInt($input.val());
			
			if ($btn.data('dir') === 'up') {
				qty++;
			} else {
				const min_qty = parseInt($btn.data('min-qty')) || 1;
				if (qty > min_qty) {
					qty--;
				} else if (min_qty === 1) {
					// Only allow reducing to 0 if min_qty is 1
					qty = 0;
				} else {
					// Stay at minimum
					return;
				}
			}
			
			shopping_cart.shopping_cart_update({
				item_code: item_code,
				qty: qty
			});
		});

		// Bind Remove Button
		$("#cart-drawer-items .btn-remove-item").on('click', function() {
			const item_code = $(this).data('item-code');
			shopping_cart.shopping_cart_update({
				item_code: item_code,
				qty: 0
			});
		});

		// Bind Remove Coupon Button
		$("#cart-drawer-summary .btn-remove-coupon").on('click', function() {
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.remove_coupon_code",
				callback: function(r) {
					if (r.message) {
						shopping_cart.show_coupon_message(__("Coupon removed."), "info");
						shopping_cart.refresh_drawer();
					}
				}
			});
		});
	}
});

// Global Event Listeners for Drawer
$(document).on('click', '.cart-drawer-close, #cart-drawer-backdrop', function() {
	$("#cart-drawer").removeClass("open");
	$("#cart-drawer-backdrop").removeClass("open");
});

$(document).on('click', '.btn-apply-coupon', function() {
	const coupon_code = $(".txtcoupon").val();
	if (!coupon_code) return;
	shopping_cart.show_coupon_message(__("Applying coupon..."), "info");
	
	frappe.call({
		method: "webshop.webshop.shopping_cart.cart.apply_coupon_code",
		args: {
			applied_code: coupon_code,
			applied_referral_sales_partner: ""
		},
		callback: function(r) {
			if (r.message) {
				shopping_cart.show_coupon_message(__("Coupon applied successfully."), "success");
				shopping_cart.refresh_drawer();
			}
		},
		error: function() {
			shopping_cart.show_coupon_message(__("Unable to apply this coupon."), "danger");
		}
	});
});
