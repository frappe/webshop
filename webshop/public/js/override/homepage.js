frappe.ui.form.on('Homepage', {
	setup: function(frm) {
		frm.set_query('item_code', 'products', function() {
			return {
				filters: {'published': 1}
			};
		});
	},
});

frappe.ui.form.on('Homepage Featured Product', {
	view: function(frm, cdt, cdn) {
		var child= locals[cdt][cdn];
		if (child.item_code && child.route) {
			window.open('/' + child.route, '_blank');
		}
	}
});
