# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.database.database import savepoint

from webshop.webshop.utils.store import (
	get_active_store_context,
	get_default_store,
	get_published_stores,
	get_store_by_slug,
	is_multi_store_enabled,
	set_store_cookies,
)


@frappe.whitelist(allow_guest=True)
def list_stores() -> dict:
	if not is_multi_store_enabled():
		return {"stores": []}

	stores = [
		{
			"slug": store.slug,
			"name": store.store_name,
			"description": store.store_description,
			"sort_order": store.sort_order,
		}
		for store in get_published_stores()
	]
	return {"stores": stores}


@frappe.whitelist(allow_guest=True)
def get_active_store() -> dict:
	store = get_active_store_context()
	if store:
		return {"store": _serialize_store(store)}

	default_store = get_default_store()
	return {"store": _serialize_store(default_store) if default_store else None}


@frappe.whitelist(allow_guest=True)
def set_active_store(slug: str) -> dict:
	if not is_multi_store_enabled():
		return {"ok": False, "error": _("Multi-store storefront is not enabled.")}

	store = get_store_by_slug(slug)
	if not store:
		return {
			"ok": False,
			"error": _("The selected store is not available. Please choose another store."),
		}

	try:
		with savepoint():
			set_store_cookies(store)
			_reprice_cart_for_store()
	except Exception:
		frappe.log_error(
			title="Store Switch Failed",
			message=frappe.get_traceback(),
		)
		return {
			"ok": False,
			"error": _("We could not switch stores right now. Please try again."),
		}

	return {"ok": True, "store": _serialize_store(store)}


def _serialize_store(store_ctx) -> dict:
	if not store_ctx:
		return {}

	if isinstance(store_ctx, dict):
		slug = store_ctx.get("slug")
		name = store_ctx.get("store_name")
		warehouse = store_ctx.get("warehouse")
		price_list = store_ctx.get("price_list")
		cost_center = store_ctx.get("cost_center")
	else:
		slug = store_ctx.slug
		name = store_ctx.store_name
		warehouse = store_ctx.warehouse
		price_list = store_ctx.price_list
		cost_center = store_ctx.cost_center

	return {
		"slug": slug,
		"name": name,
		"warehouse": warehouse,
		"price_list": price_list,
		"cost_center": cost_center,
	}


def _reprice_cart_for_store() -> None:
	if frappe.session.user == "Guest":
		return

	try:
		from webshop.webshop.shopping_cart.cart import _get_cart_quotation, apply_cart_settings
	except ImportError:
		return

	quotation = _get_cart_quotation()
	if not quotation or quotation.get("__islocal"):
		return

	apply_cart_settings(quotation=quotation)
	quotation.flags.ignore_permissions = True
	quotation.save()
