import frappe
from frappe.utils import cint

from webshop.webshop.product_data_engine.filters import ProductFiltersBuilder
from webshop.webshop.seo import add_json_ld, collection_schema, set_page_seo, website_schema

sitemap = 1


def get_context(context):
	# Add homepage as parent
	context.body_class = "product-page"
	context.parents = [{"name": frappe._("Home"), "route": "/"}]

	filter_engine = ProductFiltersBuilder()
	context.field_filters = filter_engine.get_field_filters()
	context.attribute_filters = filter_engine.get_attribute_filters()

	context.page_length = (
		cint(frappe.db.get_single_value("Webshop Settings", "products_per_page")) or 20
	)
	set_page_seo(
		context,
		frappe._("Plastic Products Online in Pakistan | Euro Plast"),
		frappe._("Shop Euro Plast kitchen, storage, bathroom, basket, and household plastic products online in Pakistan."),
		"/all-products",
		og_type="website",
	)
	add_json_ld(
		context,
		website_schema(),
		collection_schema(
			frappe._("All Euro Plast Products"),
			frappe._("Browse Euro Plast plastic household products by category, use, and price."),
			"/all-products",
		),
	)

	context.no_cache = 1
