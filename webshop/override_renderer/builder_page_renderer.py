
import frappe
from builder.builder.doctype.builder_page.builder_page import BuilderPageRenderer
from frappe.utils.caching import redis_cache
from frappe.website.path_resolver import evaluate_dynamic_routes
from builder.utils import (
	ColonRule
)

class ThemedBuilderPageRenderer(BuilderPageRenderer):
    def can_render(self):
        print("ThemedBuilderPageRenderer can_render called")
        if page := find_page_with_path(self.path):
            self.doctype = "Builder Page"
            self.docname = page
            self.validate_access()
            return True
        for d in get_web_pages_with_dynamic_routes():
            try:
                if evaluate_dynamic_routes([ColonRule(f"/{d.route}", endpoint=d.name)], self.path):
                    self.doctype = "Builder Page"
                    self.docname = d.name
                    self.validate_access()
                    return True
            except ValueError:
                print("Falling back to super().can_render()")
                return super().can_render()
        return super().can_render()

def find_page_with_path(route):
	try:
		selected_theme = get_selected_theme()
		return frappe.db.get_value("Builder Page", dict(route=route, published=1, project_folder=selected_theme), "name", cache=True) if selected_theme else frappe.db.get_value("Builder Page", dict(route=route, published=1), "name", cache=True)
	except frappe.DoesNotExistError:
		pass


@redis_cache(ttl=60 * 60)
def get_web_pages_with_dynamic_routes() -> dict[str, str]:
    selected_theme = get_selected_theme()
    return frappe.get_all(
		"Builder Page",
		fields=["name", "route", "modified"],
		filters=dict(published=1, dynamic_route=1, project_folder=selected_theme) if selected_theme else dict(published=1, dynamic_route=1),
		update={"doctype": "Builder Page"},
	)

def get_selected_theme():
    """Get the selected theme for the Builder app."""
    try:
        selected_theme = frappe.db.get_single_value("Webshop Settings", "chosen_theme")
    except frappe.DoesNotExistError:
        selected_theme = ""
    print(f"Selected theme: {selected_theme}")
    return selected_theme
