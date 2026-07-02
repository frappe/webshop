const ws_escape_html = (value) => {
	if (frappe.utils && frappe.utils.escape_html) {
		return frappe.utils.escape_html(String(value || ""));
	}
	return $("<div>").text(value || "").html();
};

const ws_escape_url = (value) => ws_escape_html(encodeURI(value || "#"));

webshop.ProductGrid = class {
	/* Options:
		- items: Items
		- settings: Webshop Settings
		- products_section: Products Wrapper
		- preference: If preference is not grid view, render but hide
	*/
	constructor(options) {
		Object.assign(this, options);

		if (this.preference !== "Grid View") {
			this.products_section.addClass("hidden");
		}

		this.products_section.empty();
		this.make();
	}

	make() {
		let me = this;
		let html = ``;

		this.items.forEach(item => {
			let title = item.web_item_name || item.item_name || item.item_code || "";
			title =  title.length > 90 ? title.substr(0, 90) + "..." : title;
			let safe_title = ws_escape_html(title);

			html += `<div class="col-sm-4 item-card"><div class="card text-left">`;
			html += me.get_image_html(item, title, safe_title);
			html += me.get_card_body_html(item, title, safe_title, me.settings);
			html += `</div></div>`;
		});

		let $product_wrapper = this.products_section;
		$product_wrapper.append(html);
	}

	get_image_html(item, title, safe_title) {
		let image = ws_escape_url(item.website_image);
		let route = ws_escape_url(item.route);

		if (item.website_image) {
			return `
				<div class="card-img-container">
					<a href="/${ route }" style="text-decoration: none;">
						<img itemprop="image" class="card-img" src="${ image }" alt="${ safe_title }">
					</a>
				</div>
			`;
		} else {
			return `
				<div class="card-img-container">
					<a href="/${ route }" style="text-decoration: none;">
						<div class="card-img-top no-image">
							${ ws_escape_html(frappe.get_abbr(title)) }
						</div>
					</a>
				</div>
			`;
		}
	}

	get_card_body_html(item, title, safe_title, settings) {
		let body_html = `
			<div class="card-body text-left card-body-flex" style="width:100%">
				<div style="margin-top: 1rem; display: flex;">
		`;
		body_html += this.get_title(item, safe_title);

		// get floating elements
		if (!item.has_variants) {
			if (settings.enable_wishlist) {
				body_html += this.get_wishlist_icon(item);
			}
			if (settings.enabled) {
				body_html += this.get_cart_indicator(item);
			}

		}

		body_html += `</div>`;
		body_html += `<div class="product-category" itemprop="name">${ ws_escape_html(item.item_group) }</div>`;

		if (item.formatted_price) {
			body_html += this.get_price_html(item);
		}

		body_html += this.get_stock_availability(item, settings);
		body_html += this.get_primary_button(item, settings);
		body_html += `</div>`; // close div on line 49

		return body_html;
	}

	get_title(item, title) {
		let route = ws_escape_url(item.route);
		let title_html = `
			<a href="/${ route }">
				<div class="product-title" itemprop="name">
					${ title || '' }
				</div>
			</a>
		`;
		return title_html;
	}

	get_wishlist_icon(item) {
		let icon_class = item.wished ? "wished" : "not-wished";
		let item_code = ws_escape_html(item.item_code);
		return `
			<div class="like-action ${ item.wished ? "like-action-wished" : ''}"
				data-item-code="${ item_code }">
				<svg class="icon sm">
					<use class="${ icon_class } wish-icon" href="#icon-heart"></use>
				</svg>
			</div>
		`;
	}

	get_cart_indicator(item) {
		let item_code = ws_escape_html(item.item_code);
		return `
			<div class="cart-indicator ${item.in_cart ? '' : 'hidden'}" data-item-code="${ item_code }">
				1
			</div>
		`;
	}

	get_price_html(item) {
		let price_html = `
			<div class="product-price" itemprop="offers" itemscope itemtype="https://schema.org/AggregateOffer">
					${ ws_escape_html(item.formatted_price) }
		`;

		if (item.formatted_mrp || item.discount) {
			if (item.formatted_mrp) {
				price_html += `
					<small class="striked-price">
						<s>${ item.formatted_mrp ? ws_escape_html(item.formatted_mrp.replace(/ +/g, "")) : "" }</s>
					</small>
				`;
			}
			price_html += `
				<small class="ml-1 product-info-green">
					${ ws_escape_html(item.discount || __("SALE")) }
				</small>
			`;
		}
		price_html += `</div>`;
		return price_html;
	}

	get_stock_availability(item, settings) {
		if (settings.show_stock_availability && !item.has_variants) {
			if (item.on_backorder) {
				return `
					<span class="out-of-stock mb-2 mt-1" style="color: var(--primary-color)">
						${ __("Available on backorder") }
					</span>
				`;
			} else if (!item.in_stock) {
				return `
					<span class="out-of-stock mb-2 mt-1">
						${ __("Out of stock") }
					</span>
				`;
			}
		}

		return ``;
	}

	get_primary_button(item, settings) {
		let route = ws_escape_url(item.route);
		let item_name = ws_escape_html(item.name);
		let item_code = ws_escape_html(item.item_code);
		if (item.has_variants) {
			return `
				<a href="/${ route }">
					<div class="btn btn-sm btn-explore-variants w-100 mt-4">
						${ __("Explore") }
					</div>
				</a>
			`;
		} else if (settings.enabled && (settings.allow_items_not_in_stock || item.in_stock)) {
			return `
				<div id="grid-add-${ item_name }" class="btn
					btn-sm btn-primary btn-add-to-cart-list
					w-100 mt-2 ${ item.in_cart ? 'hidden' : '' }"
					data-item-code="${ item_code }">
					<span class="mr-2">
						<svg class="icon icon-md">
							<use href="#icon-assets"></use>
						</svg>
					</span>
					${ settings.enable_checkout ? __("Add to Cart") :  __("Add to Quote") }
				</div>

				<a href="/cart">
					<div id="grid-cart-${ item_name }" class="btn
						btn-sm btn-primary btn-add-to-cart-list
						w-100 mt-4 go-to-cart-grid
						${ item.in_cart ? '' : 'hidden' }"
						data-item-code="${ item_code }">
						${ settings.enable_checkout ? __("Go to Cart") :  __("Go to Quote") }
					</div>
				</a>
			`;
		} else {
			return ``;
		}
	}
};
