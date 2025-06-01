if (!window.webshop) window.webshop = {};
if (!frappe.boot) frappe.boot = {};

frappe.ready(() => {
	// if (window.innerWidth < 768 && !document.querySelector(".mobile-bottom-nav")) {
	if ( !document.querySelector(".mobile-bottom-nav")) {
		const footerHTML = `
			<div class="mobile-bottom-nav">
				<a href="/shop-by-category" class="nav-item">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="icon icon-sm bi bi-collection" viewBox="0 0 16 16">
						<path d="M2.5 3.5a.5.5 0 0 1 0-1h11a.5.5 0 0 1 0 1zm2-2a.5.5 0 0 1 0-1h7a.5.5 0 0 1 0 1zM0 13a1.5 1.5 0 0 0 1.5 1.5h13A1.5 1.5 0 0 0 16 13V6a1.5 1.5 0 0 0-1.5-1.5h-13A1.5 1.5 0 0 0 0 6zm1.5.5A.5.5 0 0 1 1 13V6a.5.5 0 0 1 .5-.5h13a.5.5 0 0 1 .5.5v7a.5.5 0 0 1-.5.5z"/>
					</svg>
					<span>Category</span>
				</a>
				<a href="/all-products" class="nav-item">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="icon icon-sm bi bi-bag" viewBox="0 0 16 16">
						<path d="M8 1a2.5 2.5 0 0 1 2.5 2.5V4h-5v-.5A2.5 2.5 0 0 1 8 1m3.5 3v-.5a3.5 3.5 0 1 0-7 0V4H1v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V4zM2 5h12v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z"/>
					</svg>
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
						<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="icon icon-sm bi bi-cart" viewBox="0 0 16 16">
							<path d="M0 1.5A.5.5 0 0 1 .5 1H2a.5.5 0 0 1 .485.379L2.89 3H14.5a.5.5 0 0 1 .491.592l-1.5 8A.5.5 0 0 1 13 12H4a.5.5 0 0 1-.491-.408L2.01 3.607 1.61 2H.5a.5.5 0 0 1-.5-.5M3.102 4l1.313 7h8.17l1.313-7zM5 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4m7 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4m-7 1a1 1 0 1 1 0 2 1 1 0 0 1 0-2m7 0a1 1 0 1 1 0 2 1 1 0 0 1 0-2"/>
						</svg>
						<span>Cart</span>
						<span class="badge badge-primary shopping-badge" id="cart-count-mobile"></span>
					</a>
				</li>
				<a href="/me" class="nav-item">
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="icon icon-sm  bi bi-person-circle" viewBox="0 0 16 16">
						<path d="M11 6a3 3 0 1 1-6 0 3 3 0 0 1 6 0"/>
						<path fill-rule="evenodd" d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8m8-7a7 7 0 0 0-5.468 11.37C3.242 11.226 4.805 10 8 10s4.757 1.225 5.468 2.37A7 7 0 0 0 8 1"/>
					</svg>
					<span>Account</span>
				</a>
			</div>
		`;
		document.body.insertAdjacentHTML("beforeend", footerHTML);
	}

	document.body.addEventListener("click", (e) => {
		const btn = e.target.closest(".btn-add-to-cart-list");
		if (btn) {
			setTimeout(syncNavCountsToFooter, 200);
		}
	});

	document.body.addEventListener("click", (e) => {
		const icon = e.target.closest(".like-action");
		if (icon && icon.dataset.itemCode) {
			e.preventDefault();
			e.stopPropagation();
			icon.click();
			setTimeout(syncNavCountsToFooter, 200);
		}
	});

	syncNavCountsToFooter();
	setInterval(syncNavCountsToFooter, 2000);
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
