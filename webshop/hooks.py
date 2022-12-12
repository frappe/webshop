from . import __version__ as _version

app_name = "webshop"
app_title = "Webshop"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Open Source eCommerce Platform"
app_email = "contact@frappe.io"
app_license = "GNU General Public License (v3)"
app_version = _version

after_install = "webshop.setup.install.after_install"
on_logout = "webshop.webshop.shopping_cart.utils.clear_cart_count"
on_session_creation = [
    "webshop.webshop.utils.portal.foobar",
    "webshop.webshop.shopping_cart.utils.set_cart_count",
]
update_website_context = [
    "webshop.webshop.shopping_cart.utils.update_website_context",
]
my_account_context = "webshop.webshop.shopping_cart.utils.update_my_account_context"

website_generators = ["Website Item"]

doc_events = {
    "Sales Taxes and Charges Template": {
        "on_update": "webshop.webshop.doctype.webshop_settings.webshop_settings.validate_cart_settings"
    },
}
