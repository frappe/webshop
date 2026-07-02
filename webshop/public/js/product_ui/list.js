const ws_escape_html = (value) => {
	if (frappe.utils && frappe.utils.escape_html) {
		return frappe.utils.escape_html(String(value || ""));
	}
	return $("<div>").text(value || "").html();
};

const ws_escape_url = (value) => ws_escape_html(encodeURI(value || "#"));

const ws_badge_html = (item) => {
	if (!item.badge_label) return "";
	const label = ws_escape_html(item.badge_label);
	const color = ws_escape_html(item.badge_color || "#B0008E");
	return `<span class="badge badge-pill mb-2" style="background:${color}; color:#fff; font-size:11px; width:fit-content;">${label}</span>`;
};

webshop.ProductList = class {
	/* Options:
		- items: Items
		- settings: Webshop Settings
		- products_section: Products Wrapper
		- preference: If preference is not list view, render but hide
	*/
	constructor(options) {
		Object.assign(this, options);

		if (this.preference !== "List View") {
			this.products_section.addClass("hidden");
		}

		this.products_section.empty();
		this.make();
	}

	make() {
		let me = this;
		let html = `<br><br>`;

		this.items.forEach(item => {
			let title = item.web_item_name || item.item_name || item.item_code || "";
			title =  title.length > 200 ? title.substr(0, 200) + "..." : title;
			let safe_title = ws_escape_html(title);

			html += `<div class='row list-row w-100 mb-4'>`;
			html += me.get_image_html(item, title, safe_title, me.settings);
			html += me.get_row_body_html(item, safe_title, me.settings);
			html += `</div>`;
		});

		let $product_wrapper = this.products_section;
		$product_wrapper.append(html);
	}

	get_image_html(item, title, safe_title, settings) {
		let image = ws_escape_url(item.website_image);
		let route = ws_escape_url(item.route);
		let wishlist_enabled = !item.has_variants && settings.enable_wishlist;
		let image_html = ``;

		if (item.website_image) {
			image_html += `
				<div class="col-2 border text-center rounded list-image">
					<a class="product-link product-list-link" href="/${ route }">
						<img itemprop="image" class="website-image h-100 w-100" alt="${ safe_title }"
							src="${ image }">
					</a>
					${ wishlist_enabled ? this.get_wishlist_icon(item): '' }
				</div>
			`;
		} else {
			image_html += `
				<div class="col-2 border text-center rounded list-image">
					<a class="product-link product-list-link" href="/${ route }"
						style="text-decoration: none">
					<div class="card-img-top no-image-list">
						${ ws_escape_html(frappe.get_abbr(title)) }
					</div>
					</a>
					${ wishlist_enabled ? this.get_wishlist_icon(item): '' }
				</div>
			`;
		}

		return image_html;
	}

	get_row_body_html(item, title, settings) {
		let body_html = `<div class='col-10 text-left'>`;
		body_html += this.get_title_html(item, title, settings);
		body_html += this.get_item_details(item, settings);
		body_html += `</div>`;
		return body_html;
	}

	get_title_html(item, title, settings) {
		let route = ws_escape_url(item.route);
		let title_html = `<div style="display: flex; margin-left: -15px;">`;
		title_html += `
			<div class="col-8" style="margin-right: -15px;">
				<a class="" href="/${ route }"
					style="color: var(--gray-800); font-weight: 500;">
					${ title }
				</a>
			</div>
		`;

		if (settings.enabled) {
			title_html += `<div class="col-4 cart-action-container ${item.in_cart ? 'd-flex' : ''}">`;
			title_html += this.get_primary_button(item, settings);
			title_html += `</div>`;
		}
		title_html += `</div>`;

		return title_html;
	}

	get_item_details(item, settings) {
		let details = `
			${ ws_badge_html(item) }
			<p class="product-code">
				${ ws_escape_html(item.item_group) } | ${ __('Item Code') } : ${ ws_escape_html(item.item_code) }
			</p>
			<div class="mt-2" style="color: var(--gray-600) !important; font-size: 13px;">
				${ ws_escape_html(item.short_description) }
			</div>
			<div class="product-price" itemprop="offers" itemscope itemtype="https://schema.org/AggregateOffer">
				${ ws_escape_html(item.formatted_price) }
		`;

		if (item.formatted_mrp || item.discount) {
			if (item.formatted_mrp) {
				details += `
					<small class="striked-price">
						<s>${ item.formatted_mrp ? ws_escape_html(item.formatted_mrp.replace(/ +/g, "")) : "" }</s>
					</small>
				`;
			}
			details += `
				<small class="ml-1 product-info-green">
					${ ws_escape_html(item.discount || __("SALE")) }
				</small>
			`;
		}

		details += this.get_stock_availability(item, settings);
		details += `</div>`;

		return details;
	}

	get_stock_availability(item, settings) {
		if (settings.show_stock_availability && !item.has_variants) {
			if (item.on_backorder) {
				return `
					<br>
					<span class="out-of-stock mt-2" style="color: var(--primary-color)">
						${ __("Available on backorder") }
					</span>
				`;
			} else if (!item.in_stock) {
				return `
					<br>
					<span class="out-of-stock mt-2">${ __("Out of stock") }</span>
				`;
			} else if (item.is_stock) {
				return `
					<br>
					<span class="in-stock in-green has-stock mt-2"
						style="font-size: 14px;">${ __("In stock") }</span>
				`;
			}
		}
		return ``;
	}

	get_wishlist_icon(item) {
		let icon_class = item.wished ? "wished" : "not-wished";
		let item_code = ws_escape_html(item.item_code);

		return `
			<div class="like-action-list ${ item.wished ? "like-action-wished" : ''}"
				data-item-code="${ item_code }">
				<svg class="icon sm">
					<use class="${ icon_class } wish-icon" href="#icon-heart"></use>
				</svg>
			</div>
		`;
	}

	get_primary_button(item, settings) {
		let route = ws_escape_url(item.route);
		let item_name = ws_escape_html(item.name);
		let item_code = ws_escape_html(item.item_code);
		if (item.has_variants) {
			return `
				<a href="/${ route }">
					<div class="btn btn-sm btn-explore-variants btn mb-0 mt-0">
						${ __("Explore") }
					</div>
				</a>
			`;
		} else if (settings.enabled && (settings.allow_items_not_in_stock || item.in_stock)) {
			return `
				<div id="list-add-${ item_name }" class="btn
					btn-sm btn-primary btn-add-to-cart-list mb-0
					${ item.in_cart ? 'hidden' : '' }"
					data-item-code="${ item_code }"
					style="margin-top: 0px !important; max-height: 30px; float: right;
						padding: 0.25rem 1rem; min-width: 135px;">
					<span class="mr-2">
						<svg class="icon icon-md">
							<use href="#icon-assets"></use>
						</svg>
					</span>
					${ settings.enable_checkout ? __("Add to Cart") :  __("Add to Quote") }
				</div>

				<div class="cart-indicator list-indicator ${item.in_cart ? '' : 'hidden'}">
					1
				</div>

				<a href="/cart">
					<div id="list-cart-${ item_name }" class="btn
						btn-sm btn-primary btn-add-to-cart-list
						ml-4 go-to-cart mb-0 mt-0
						${ item.in_cart ? '' : 'hidden' }"
						data-item-code="${ item_code }"
						style="padding: 0.25rem 1rem; min-width: 135px;">
						${ settings.enable_checkout ? __("Go to Cart") :  __("Go to Quote") }
					</div>
				</a>
			`;
		} else {
			return ``;
		}
	}

};
