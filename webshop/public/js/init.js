if (!window.webshop) window.webshop = {};
if (!frappe.boot) frappe.boot = {};

frappe.ready(() => {
	if (window.innerWidth < 768 && !document.querySelector(".mobile-bottom-nav")) {
		const footerHTML = `
			<div class="mobile-bottom-nav">
				<a href="/shop-by-category" class="nav-item">
					<svg class="icon icon-sm"><use href="#icon-grid" /></svg>
					<span>Category</span>
				</a>
				<a href="/all-products" class="nav-item">
					<svg class="icon icon-sm"><use href="#icon-box" /></svg>
					<span>Products</span>
				</a>
				<li class="wishlist wishlist-icon hidden nav-item">
					<a class="nav-link" href="/wishlist">
						<svg class="icon icon-sm"><use href="#icon-heart" /></svg>
						<span>Favorites</span>
						<span class="badge badge-primary shopping-badge" id="wish-count-mobile"></span>
					</a>
				</li>
				<li class="shopping-cart cart-icon hidden nav-item">
					<a class="nav-link" href="/cart">
						<svg class="icon icon-sm"><use href="#icon-assets" /></svg>
						<span>Cart</span>
						<span class="badge badge-primary shopping-badge" id="cart-count-mobile"></span>
					</a>
				</li>
				<a href="/me" class="nav-item">
					<svg class="icon icon-sm"><use href="#icon-user" /></svg>
					<span>Account</span>
				</a>
			</div>
		`;
		document.body.insertAdjacentHTML("beforeend", footerHTML);
	}

	document.body.addEventListener("click", (e) => {
		const btn = e.target.closest(".btn-add-to-cart-list");
		if (btn) {
			setTimeout(syncNavCountsToFooter, 1000);
		}
	});

	document.body.addEventListener("click", (e) => {
		const icon = e.target.closest(".like-action");
		if (icon && icon.dataset.itemCode) {
			e.preventDefault();
			e.stopPropagation();
			icon.click();
			setTimeout(syncNavCountsToFooter, 800);
		}
	});

	setInterval(syncNavCountsToFooter, 10000);
	syncNavCountsToFooter();
});

function syncNavCountsToFooter() {
	const cartTop = document.querySelector("#cart-count");
	const cartMobile = document.querySelector("#cart-count-mobile");
	const cartLi = document.querySelector(".mobile-bottom-nav .cart-icon");
	if (cartTop && cartMobile) {
		const val = parseInt(cartTop.innerText || "0");
		cartMobile.innerText = val;
		cartLi?.classList.toggle("hidden", val === 0);
		cartMobile.style.display = val > 0 ? "inline-block" : "none";
	}

	const wishTop = document.querySelector("#wish-count");
	const wishMobile = document.querySelector("#wish-count-mobile");
	const wishLi = document.querySelector(".mobile-bottom-nav .wishlist-icon");
	if (wishTop && wishMobile) {
		const val = parseInt(wishTop.innerText || "0");
		wishMobile.innerText = val;
		wishLi?.classList.toggle("hidden", val === 0);
		wishMobile.style.display = val > 0 ? "inline-block" : "none";
	}
}
