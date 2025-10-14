frappe.listview_settings["Website Store"] = {
	add_fields: ["is_published", "disabled"],
	get_indicator(doc) {
		if (doc.disabled) {
			return [__("Disabled"), "grey", "disabled,=,1"];
		}
		if (!doc.is_published) {
			return [__("Unpublished"), "orange", "is_published,=,0"];
		}
		return [__("Live"), "green", "is_published,=,1|disabled,=,0"];
	},
};
