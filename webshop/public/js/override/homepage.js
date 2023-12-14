frappe.ui.form.on('Homepage', {
	setup: function(frm) {
		frm.fields_dict['products'].grid.get_field('item_code').get_query = function() {
			return {
				filters: {'published': 1}
			}
		}
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
