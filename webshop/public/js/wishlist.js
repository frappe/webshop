frappe.provide("webshop.webshop.wishlist");
var wishlist = webshop.webshop.wishlist;

frappe.provide("webshop.webshop.shopping_cart");
var shopping_cart = webshop.webshop.shopping_cart;

const ws_escape_html = (value) => {
	if (frappe.utils && frappe.utils.escape_html) {
		return frappe.utils.escape_html(String(value || ""));
	}
	return $("<div>").text(value || "").html();
};

const ws_escape_url = (value) => ws_escape_html(encodeURI(value || "#"));

$.extend(wishlist, {
	set_wishlist_count: function(animate=false) {
		// set badge count for wishlist icon
		var wish_count = 0;
		if (frappe.session.user === "Guest") {
			wish_count = this.get_guest_wishlist().length;
		} else {
			wish_count = frappe.get_cookie("wish_count") || 0;
		}

		if (wish_count) {
			$(".wishlist").toggleClass('hidden', false);
		}

		var $wishlist = $('.wishlist-icon');
		var $badge = $wishlist.find("#wish-count");

		if (parseInt(wish_count) === 0 || wish_count === undefined) {
			$wishlist.css("display", "none");
		} else {
			$wishlist.css("display", "inline");
		}

		if (wish_count) {
			if ($badge.length === 0) {
				$wishlist.find('a').append('<span class="badge badge-danger shopping-badge" id="wish-count"></span>');
				$badge = $wishlist.find("#wish-count");
			}
			$badge.html(wish_count);
			if (animate) {
				$wishlist.addClass('cart-animate');
				setTimeout(() => {
					$wishlist.removeClass('cart-animate');
				}, 500);
			}
		} else {
			$badge.remove();
		}
	},

	get_guest_wishlist: function() {
		let list = localStorage.getItem("guest_wishlist");
		try {
			return list ? JSON.parse(list) : [];
		} catch (e) {
			localStorage.removeItem("guest_wishlist");
			return [];
		}
	},

	set_guest_wishlist: function(list) {
		localStorage.setItem("guest_wishlist", JSON.stringify(list));
	},

	bind_move_to_cart_action: function() {
		// move item to cart from wishlist
		$(document.body).off("click", ".btn-add-to-cart").on("click", ".btn-add-to-cart", (e) => {
			const $move_to_cart_btn = $(e.currentTarget);
			let item_code = $move_to_cart_btn.data("item-code");

			shopping_cart.shopping_cart_update({
				item_code,
				qty: 1,
				cart_dropdown: true
			});

			let success_action = function() {
				const $card_wrapper = $move_to_cart_btn.closest(".wishlist-card");
				$card_wrapper.addClass("wish-removed");
			};
			let args = { item_code: item_code };
			this.add_remove_from_wishlist("remove", args, success_action, null, true);
		});
	},

	bind_remove_action: function() {
		// remove item from wishlist
		let me = this;
		$(document.body).off("click", ".remove-wish").on("click", ".remove-wish", (e) => {
			const $remove_wish_btn = $(e.currentTarget);
			let item_code = $remove_wish_btn.data("item-code");

			let success_action = function() {
				const $card_wrapper = $remove_wish_btn.closest(".wishlist-card");
				$card_wrapper.addClass("wish-removed");
				
				let count = 0;
				if (frappe.session.user === "Guest") {
					count = me.get_guest_wishlist().length;
				} else {
					count = frappe.get_cookie("wish_count") || 0;
				}

				if (count == 0) {
					$(".page_content .products-list").empty();
					me.render_empty_state();
				}
			};
			let args = { item_code: item_code };
			this.add_remove_from_wishlist("remove", args, success_action);
		});
	},

	bind_wishlist_action() {
		// 'wish'('like') or 'unwish' item in product listing
		$(document.body).off('click', '.like-action, .like-action-list').on('click', '.like-action, .like-action-list', (e) => {
			const $btn = $(e.currentTarget);
			this.wishlist_action($btn);
		});
	},

	wishlist_action(btn) {
		const $wish_icon = btn.find('.wish-icon');
		let item_code = btn.data('item-code');
		let me = this;

		if (frappe.session.user === "Guest") {
			let list = this.get_guest_wishlist();
			if ($wish_icon.hasClass('wished')) {
				// remove
				list = list.filter(i => i !== item_code);
				this.toggle_button_class($wish_icon, 'wished', 'not-wished');
				btn.removeClass("like-animate");
				btn.removeClass("like-action-wished");
			} else {
				// add
				if (!list.includes(item_code)) {
					list.push(item_code);
				}
				this.toggle_button_class($wish_icon, 'not-wished', 'wished');
				btn.addClass("like-animate");
				btn.addClass("like-action-wished");
			}
			this.set_guest_wishlist(list);
			this.set_wishlist_count(true);
			return;
		}

		let success_action = function() {
			webshop.webshop.wishlist.set_wishlist_count(true);
		};

		if ($wish_icon.hasClass('wished')) {
			// un-wish item
			btn.removeClass("like-animate");
			btn.addClass("like-action-wished");
			this.toggle_button_class($wish_icon, 'wished', 'not-wished');

			let args = { item_code: item_code };
			let failure_action = function() {
				me.toggle_button_class($wish_icon, 'not-wished', 'wished');
			};
			this.add_remove_from_wishlist("remove", args, success_action, failure_action);
		} else {
			// wish item
			btn.addClass("like-animate");
			btn.addClass("like-action-wished");
			this.toggle_button_class($wish_icon, 'not-wished', 'wished');

			let args = {item_code: item_code};
			let failure_action = function() {
				me.toggle_button_class($wish_icon, 'wished', 'not-wished');
			};
			this.add_remove_from_wishlist("add", args, success_action, failure_action);
		}
	},

	toggle_button_class(button, remove, add) {
		button.removeClass(remove);
		button.addClass(add);
	},

	add_remove_from_wishlist(action, args, success_action, failure_action, async=false) {
		if (frappe.session.user === "Guest") {
			let list = this.get_guest_wishlist();
			if (action === "add") {
				if (!list.includes(args.item_code)) list.push(args.item_code);
			} else {
				list = list.filter(i => i !== args.item_code);
			}
			this.set_guest_wishlist(list);
			this.set_wishlist_count(true);
			if (success_action) success_action();
		} else {
			let method = "webshop.webshop.doctype.wishlist.wishlist.add_to_wishlist";
			if (action === "remove") {
				method = "webshop.webshop.doctype.wishlist.wishlist.remove_from_wishlist";
			}

			frappe.call({
				async: async,
				type: "POST",
				method: method,
				args: args,
				callback: function (r) {
					if (r.exc) {
						if (failure_action && (typeof failure_action === 'function')) {
							failure_action();
						}
						frappe.msgprint({
							message: __("Sorry, something went wrong. Please refresh."),
							indicator: "red", title: __("Note")
						});
					} else if (success_action && (typeof success_action === 'function')) {
						success_action();
					}
				}
			});
		}
	},

	redirect_guest() {
		frappe.call('webshop.webshop.api.get_guest_redirect_on_action').then((res) => {
			window.location.href = res.message || "/login";
		});
	},

	render_empty_state() {
		$(".page_content").html(`
			<div class="cart-empty frappe-card">
				<div class="cart-empty-state">
					<img src="/assets/webshop/images/cart-empty-state.png" alt="Empty Cart">
				</div>
				<div class="cart-empty-message mt-4">${ __('Wishlist is empty!') }</p>
			</div>
		`);
	},

	initialize_guest_wishlist_icons: function() {
		if (frappe.session.user !== "Guest") return;
		let list = this.get_guest_wishlist();
		$('.like-action, .like-action-list').each(function() {
			let item_code = $(this).data('item-code');
			if (list.includes(item_code)) {
				let $icon = $(this).find('.wish-icon');
				$icon.removeClass('not-wished').addClass('wished');
				$(this).addClass('like-action-wished');
			}
		});
	},

	render_guest_wishlist_page: function() {
		if (frappe.session.user !== "Guest" || window.location.pathname !== "/wishlist") return;
		
		let list = this.get_guest_wishlist();
		if (list.length === 0) {
			this.render_empty_state();
			return;
		}

		$(".page_content").html('<div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div></div>');

		frappe.call({
			method: "webshop.webshop.api.get_wishlist_items_details",
			args: { item_codes: list },
			callback: (r) => {
				if (r.message && r.message.length > 0) {
					this.render_wishlist_items(r.message);
				} else {
					this.render_empty_state();
				}
			},
			error: (r) => {
				$(".page_content").html(`
					<div class="alert alert-danger m-5 text-center">
						${__("Failed to load wishlist items. Please try again later.")}
					</div>
				`);
			}
		});
	},

	render_wishlist_items: function(items) {
		let html = `<div class="row">
			<div class="col-md-12 item-card-group-section">
				<div class="row products-list">`;
		
		items.forEach(item => {
			html += this.get_wishlist_card_html(item);
		});

		html += `</div></div></div>`;
		$(".page_content").html(html);
	},

	get_wishlist_card_html: function(item) {
		// Simplified version of the wishlist_card macro
		let item_code = ws_escape_html(item.item_code);
		let item_name = ws_escape_html(item.item_name);
		let web_item_name = ws_escape_html(item.web_item_name || item.item_name);
		let item_group = ws_escape_html(item.item_group);
		let route = ws_escape_url(item.route);
		let image_html = item.image ? 
			`<img itemprop="image" class="card-img" src="${ws_escape_url(item.image)}" alt="${web_item_name}">` :
			`<div itemprop="image" class="card-img-top no-image">${item.item_name ? ws_escape_html(item.item_name.substring(0,2).toUpperCase()) : 'NA'}</div>`;

		let price_html = `<div class="product-price">${ws_escape_html(item.formatted_price)}`;
		if (item.formatted_mrp) {
			price_html += `<small class="ml-1 striked-price"><s>${ws_escape_html(item.formatted_mrp)}</s></small>
						   <small class="ml-1 product-info-green">${ws_escape_html(item.discount)} OFF</small>`;
		}
		price_html += `</div>`;

		let action_html = item.available ? 
			`<button data-item-code="${item_code}" class="btn btn-primary btn-add-to-cart-list btn-add-to-cart mt-2 w-100">
				<span class="mr-2"><svg class="icon icon-md"><use href="#icon-assets"></use></svg></span>
				${__("Move to Cart")}
			</button>` :
			`<div class="out-of-stock">${__("Out of stock")}</div>`;

		return `
				<div class="col-sm-3 wishlist-card">
					<div class="card text-center">
						<div class="card-img-container">
							<a href="/${route}" style="text-decoration: none;">
								${image_html}
							</a>
							<div class="remove-wish" data-item-code="${item_code}">
								<svg class="icon icon-md remove-wish-icon">
								<use class="close" href="#icon-delete"></use>
							</svg>
							</div>
						</div>
						<div class="card-body card-body-flex text-left" style="width: 100%;">
							<div class="mt-4">
								<div class="product-title">${web_item_name || item_name}</div>
								<div class="product-category">${item_group || ''}</div>
							</div>
						${price_html}
						${action_html}
					</div>
				</div>
			</div>
		`;
	}
});

frappe.ready(function() {
	wishlist.set_wishlist_count();
	wishlist.initialize_guest_wishlist_icons();

	if (window.location.pathname === "/wishlist") {
		wishlist.bind_move_to_cart_action();
		wishlist.bind_remove_action();
		if (frappe.session.user === "Guest") {
			wishlist.render_guest_wishlist_page();
		}
	} else {
		wishlist.bind_wishlist_action();
	}
});
