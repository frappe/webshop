frappe.provide("webshop.webshop.conversion");

webshop.webshop.conversion = {
	settings: null,

	init() {
		this.inject_styles();
		this.fetch_settings();
		this.bind_coupon_copy();
		this.bind_whatsapp_assist();
		this.setup_product_page();
		this.setup_exit_intent();
	},

	inject_styles() {
		if ($("#conversion-booster-styles").length) return;
		$("head").append(`
			<style id="conversion-booster-styles">
				.conversion-rating-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border:1px solid #e2e8f0;border-radius:6px;background:#fff;color:#1f2937;text-decoration:none}
				.conversion-stars,.conversion-card-rating{color:#f59e0b;letter-spacing:0;font-size:12px}
				.conversion-promise-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
				.conversion-promise{border:1px solid #e2e8f0;background:#f8fafc;border-radius:6px;padding:10px;font-size:12px;color:#475569}
				.conversion-promise strong{display:block;color:#111827;font-size:13px;margin-bottom:2px}
				.conversion-strip{margin-top:24px}
				.conversion-strip-title{font-weight:700;font-size:18px;margin-bottom:12px}
				.conversion-strip-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
				.conversion-product-card{display:block;border:1px solid #e5e7eb;border-radius:8px;background:#fff;padding:12px;text-decoration:none;color:#111827;min-height:100%}
				.conversion-card-image{height:120px;display:flex;align-items:center;justify-content:center;background:#f8fafc;border-radius:6px;margin-bottom:10px}
				.conversion-card-image img{max-width:100%;max-height:112px;object-fit:contain}
				.conversion-card-title{font-weight:600;font-size:13px;line-height:1.35;min-height:36px}
				.conversion-card-price{margin-top:6px;font-weight:700;color:var(--primary)}
				.ws-sticky-buy-bar{display:none}
				.conversion-checkout-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin-bottom:18px}
				.conversion-step{padding:10px;border:1px solid #e5e7eb;border-radius:6px;background:#fff;font-size:12px;font-weight:700;color:#475569;text-align:center}
				.conversion-step.active{background:rgba(var(--primary-rgb),.08);border-color:var(--primary);color:var(--primary)}
				@media(max-width:767px){
					body{padding-bottom:76px}
					.ws-sticky-buy-bar{position:fixed;left:0;right:0;bottom:0;z-index:1040;display:flex;align-items:center;gap:8px;padding:10px 12px;background:#fff;border-top:1px solid #e5e7eb;box-shadow:0 -8px 24px rgba(15,23,42,.12)}
					.ws-sticky-buy-meta{min-width:0;flex:1}
					.ws-sticky-buy-title{font-size:12px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
					.ws-sticky-buy-price{font-size:13px;font-weight:800;color:var(--primary)}
					.ws-sticky-buy-bar .btn{height:42px;padding:0 12px;border-radius:6px;font-size:13px;font-weight:700}
					.conversion-promise-grid,.conversion-strip-grid{grid-template-columns:1fr}
				}
			</style>
		`);
	},

	fetch_settings() {
		frappe.call({
			method: "webshop.webshop.api.get_conversion_settings",
			callback: (r) => {
				this.settings = r.message || {};
			}
		});
	},

	escape_html(value) {
		if (frappe.utils && frappe.utils.escape_html) {
			return frappe.utils.escape_html(String(value || ""));
		}
		return $("<div>").text(value || "").html();
	},

	escape_url(value) {
		return this.escape_html(encodeURI(value || "#"));
	},

	setup_product_page() {
		const $cart = $(".item-cart[data-variant-item-code]");
		if (!$cart.length) return;

		const item_code = $cart.data("variant-item-code");
		this.track_recently_viewed(item_code);
		this.render_sticky_buy_bar();
		this.render_review_summary(item_code);
		this.render_recently_viewed(item_code);
		this.render_recommendations(item_code);
	},

	track_recently_viewed(item_code) {
		if (!item_code) return;
		let items = [];
		try {
			items = JSON.parse(localStorage.getItem("recently_viewed_items") || "[]");
		} catch (e) {
			items = [];
		}
		items = items.filter((code) => code !== item_code);
		items.unshift(item_code);
		localStorage.setItem("recently_viewed_items", JSON.stringify(items.slice(0, 12)));
	},

	render_sticky_buy_bar() {
		if ($("#ws-sticky-buy-bar").length || !$(".btn-buy-now").length) return;

		const title = $(".product-title, h1[itemprop='name'], .page-title").first().text().trim() || document.title;
		const price = $(".product-price-section .h1").first().text().trim();
		const html = `
			<div id="ws-sticky-buy-bar" class="ws-sticky-buy-bar">
				<div class="ws-sticky-buy-meta">
					<div class="ws-sticky-buy-title">${this.escape_html(title)}</div>
					${price ? `<div class="ws-sticky-buy-price">${this.escape_html(price)}</div>` : ""}
				</div>
				<button class="btn btn-outline-primary ws-sticky-add">${__("Add")}</button>
				<button class="btn btn-primary ws-sticky-buy">${__("Buy Now")}</button>
			</div>
		`;
		$("body").append(html);
		$(".ws-sticky-add").on("click", () => $(".btn-add-to-cart").first().trigger("click"));
		$(".ws-sticky-buy").on("click", () => $(".btn-buy-now").first().trigger("click"));
	},

	render_review_summary(item_code) {
		const $target = $("#conversion-review-summary");
		if (!$target.length || !item_code) return;

		frappe.call({
			method: "webshop.webshop.api.get_item_review_summary",
			args: { item_code },
			callback: (r) => {
				const summary = r.message || {};
				if (!summary.total_reviews) {
					$target.html(`<span class="text-muted small">${__("Be the first to review this product")}</span>`);
					return;
				}
				const rating = Number(summary.average_rating || 0).toFixed(1);
				$target.html(`
					<a href="#reviews" class="conversion-rating-pill">
						<span class="conversion-stars">★★★★★</span>
						<span>${this.escape_html(rating)}</span>
						<span class="text-muted">(${this.escape_html(summary.total_reviews)} ${__("reviews")})</span>
					</a>
				`);
			}
		});
	},

	render_recently_viewed(current_item_code) {
		const $target = $("#recently-viewed-products");
		if (!$target.length) return;

		let item_codes = [];
		try {
			item_codes = JSON.parse(localStorage.getItem("recently_viewed_items") || "[]");
		} catch (e) {
			item_codes = [];
		}
		item_codes = item_codes.filter((code) => code && code !== current_item_code).slice(0, 4);
		if (!item_codes.length) return;

		frappe.call({
			method: "webshop.webshop.api.get_recently_viewed_items",
			args: { item_codes },
			callback: (r) => this.render_product_strip($target, __("Recently Viewed"), r.message || [])
		});
	},

	render_recommendations(item_code) {
		const $target = $("#smart-recommendations");
		if (!$target.length) return;

		frappe.call({
			method: "webshop.webshop.api.get_smart_recommendations",
			args: { item_code, limit: 4 },
			callback: (r) => this.render_product_strip($target, __("You May Also Like"), r.message || [])
		});
	},

	render_product_strip($target, title, items) {
		if (!items.length) return;
		const cards = items.map((item) => {
			const image = item.thumbnail || item.website_image || "/assets/webshop/images/cart-empty-state.png";
			const rating = item.review_summary && item.review_summary.total_reviews
				? `<div class="conversion-card-rating">★★★★★ ${this.escape_html(Number(item.review_summary.average_rating || 0).toFixed(1))}</div>`
				: "";
			return `
				<a class="conversion-product-card" href="/${this.escape_url(item.route)}">
					<div class="conversion-card-image"><img src="${this.escape_url(image)}" alt="${this.escape_html(item.web_item_name || item.item_name)}"></div>
					<div class="conversion-card-title">${this.escape_html(item.web_item_name || item.item_name)}</div>
					${rating}
					${item.formatted_price ? `<div class="conversion-card-price">${this.escape_html(item.formatted_price)}</div>` : ""}
				</a>
			`;
		}).join("");

		$target.html(`
			<div class="conversion-strip">
				<div class="conversion-strip-title">${this.escape_html(title)}</div>
				<div class="conversion-strip-grid">${cards}</div>
			</div>
		`);
	},

	bind_coupon_copy() {
		$(document).on("click", ".btn-copy-conversion-coupon", function() {
			const code = $(this).data("coupon");
			if (!code) return;
			navigator.clipboard && navigator.clipboard.writeText(code);
			frappe.show_alert({ message: __("Coupon copied"), indicator: "green" });
			$(".txtcoupon").val(code);
		});
	},

	bind_whatsapp_assist() {
		$(document).on("click", ".btn-whatsapp-cart-assist", function() {
			const $btn = $(this);
			$btn.prop("disabled", true);
			frappe.call({
				method: "webshop.webshop.api.get_cart_whatsapp_assist_url",
				callback: (r) => {
					$btn.prop("disabled", false);
					if (r.message && r.message.url) {
						window.open(r.message.url, "_blank", "noopener");
					}
				},
				error: () => $btn.prop("disabled", false)
			});
		});
	},

	setup_exit_intent() {
		let shown = false;
		const maybe_show = () => {
			if (shown || sessionStorage.getItem("conversion_exit_prompt_seen")) return;
			const cart_count = parseInt(frappe.get_cookie("cart_count") || 0);
			if (!cart_count || (this.settings && !this.settings.enable_exit_intent_recovery)) return;

			shown = true;
			sessionStorage.setItem("conversion_exit_prompt_seen", "1");
			frappe.confirm(
				__("Want help completing your cart on WhatsApp?"),
				() => $(".btn-whatsapp-cart-assist").first().trigger("click"),
				() => {}
			);
		};

		$(document).on("mouseleave", (e) => {
			if (e.clientY <= 0) maybe_show();
		});
	}
};

frappe.ready(() => webshop.webshop.conversion.init());
