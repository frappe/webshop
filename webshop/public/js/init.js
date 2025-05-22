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

		// مزامنة مع العدادات الأصلية
		syncNavCountsToFooter();

		// تحديث بعد الإضافة للسلة
		document.body.addEventListener("click", (e) => {
			const btn = e.target.closest(".btn-add-to-cart-list");
			if (btn) {
				setTimeout(syncNavCountsToFooter, 1000);
			}
		});

		// استخدام الكود الأصلي للنظام للإضافة للمفضلة
		document.body.addEventListener("click", (e) => {
			const icon = e.target.closest(".like-action");
			if (icon && icon.dataset.itemCode) {
				e.preventDefault();
				e.stopPropagation();
				// تفعيل الحدث بنفس الكود المستخدم في النظام
				icon.click();
				setTimeout(syncNavCountsToFooter, 800);
			}
		});

		// تحديث دوري
		setInterval(syncNavCountsToFooter, 10000);
	}
});

function syncNavCountsToFooter() {
	// مزامنة العداد مع السلة
	const cartTop = document.querySelector("#cart-count");
	const cartMobile = document.querySelector("#cart-count-mobile");
	const cartLi = document.querySelector(".mobile-bottom-nav .cart-icon");
	if (cartTop && cartMobile) {
		const val = parseInt(cartTop.innerText || "0");
		cartMobile.innerText = val;
		if (val > 0) {
			cartMobile.style.display = 'inline-block';
			cartLi && cartLi.classList.remove("hidden");
		} else {
			cartMobile.style.display = 'none';
			cartLi && cartLi.classList.add("hidden");
		}
	}

	// مزامنة العداد مع المفضلة
	const wishTop = document.querySelector("#wish-count");
	const wishMobile = document.querySelector("#wish-count-mobile");
	const wishLi = document.querySelector(".mobile-bottom-nav .wishlist-icon");
	if (wishTop && wishMobile) {
		const val = parseInt(wishTop.innerText || "0");
		wishMobile.innerText = val;
		if (val > 0) {
			wishMobile.style.display = 'inline-block';
			wishLi && wishLi.classList.remove("hidden");
		} else {
			wishMobile.style.display = 'none';
			wishLi && wishLi.classList.add("hidden");
		}
	}
}
