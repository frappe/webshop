from frappe import _


def get_data():
	return {
		"fieldname": "website_item",
		"non_standard_fieldnames": {
			"Website Collection": "website_item",
			"Website Category": "website_item",
		},
		"transactions": [
			{
				"label": _("Connections"),
				"items": [
					"Website Collection",
					"Website Category",
				],
			},
		],
	}
