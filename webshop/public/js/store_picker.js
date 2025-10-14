frappe.ready(function () {
	const picker = document.querySelector(".store-switcher-select");
	if (!picker) {
		return;
	}

	const spinner = document.querySelector(".store-switcher-spinner");
	picker.dataset.currentValue = picker.value;

	const toggleSpinner = (show) => {
		if (!spinner) {
			return;
		}
		spinner.classList.toggle("d-none", !show);
	};

	picker.addEventListener("change", () => {
		const selected = picker.value;
		const previous = picker.dataset.currentValue;

		if (!selected || selected === previous) {
			return;
		}

		picker.disabled = true;
		toggleSpinner(true);

		frappe
			.call("webshop.webshop.api.store.set_active_store", { slug: selected })
			.then((r) => {
				const response = r.message || {};
				if (response.ok) {
					window.location.reload();
					return;
				}

				throw new Error(response.error || __("Unable to switch store"));
			})
			.catch((error) => {
				const message = error?.message || __("Unable to switch store");
				frappe.show_alert({ message, indicator: "red" });
				picker.value = previous;
			})
			.finally(() => {
				picker.dataset.currentValue = picker.value;
				picker.disabled = false;
				toggleSpinner(false);
			});
	});
});
