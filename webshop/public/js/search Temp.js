frappe.ready(() => {
	const products_section = $("#product-listing");
	const preference = "Grid View"; // يمكنك لاحقًا جعله ديناميكيًا حسب تفضيل المستخدم
	const items = window.search_items || [];
	const settings = window.webshop_settings || {};

	if (items.length === 0) {
		products_section.html(`<p class="text-muted text-center">${__("لا توجد منتجات مطابقة.")}</p>`);
		return;
	}

	if (preference === "Grid View") {
		new webshop.ProductGrid({
			items,
			settings,
			products_section,
			preference,
		});
	} else {
		new webshop.ProductList({
			items,
			settings,
			products_section,
			preference,
		});
	}
});
