frappe.ready(() => {
	const query = new URLSearchParams(window.location.search).get("q");
	if (!query) return;

	document.getElementById("search-query").textContent = query;

	const view_type = localStorage.getItem("product_view") || "Grid View";

	// إزالة شريط البحث إن وجد
	const searchInput = document.getElementById("search-bar");
	if (searchInput) searchInput.style.display = "none";

	frappe.call({
		method: "webshop.api.product_search.product_search",
		args: { q: query },
		callback: function (r) {
			const results = r.message || [];
			const container = document.getElementById("results");

			if (!results.length) {
				container.innerHTML = `<p>No products found.</p>`;
				return;
			}

			container.innerHTML = "";
			container.className = view_type === "List View"
				? "row list-view"
				: "row grid-view";

			for (let item of results) {
				const title = item.web_item_name || item.item_name || "product";
				const image_url = item.website_image;
				const product_url = item.route ? `/${item.route}` : `/${item.name}`;
				const item_group = item.item_group || "";
				const initials = title.trim().substring(0, 2).toUpperCase();

				const card = document.createElement("div");
				card.className = view_type === "List View"
					? "col-12 mb-3"
					: "col-12 col-sm-6 col-md-4 col-lg-3 mb-4";

				card.innerHTML = `
					<div class="item-card ${view_type === "List View" ? "list d-flex align-items-center" : ""}">
						<div class="item-image ${view_type === "List View" ? "mr-3" : ""}">
							${
								image_url
									? `<img src="${image_url}" alt="${title}" class="img-fluid">`
									: `<div class="no-image">${initials}</div>`
							}
						</div>
						<div class="item-card-body">
							<a href="${product_url}" style="color: inherit;" class="item-title d-block mb-1">
								${title}
							</a>
							<div class="item-group text-muted">${item_group}</div>
						</div>
					</div>
				`;

				container.appendChild(card);


			}
		}
	});
});
