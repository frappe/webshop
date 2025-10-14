# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Optional

import frappe
from frappe.utils import now_datetime


COOKIE_MAX_AGE = 30 * 24 * 60 * 60
STORE_COOKIE_KEYS = ("store_slug", "store_warehouse", "store_price_list")


@dataclass(frozen=True)
class StoreContext:
	name: str
	slug: str
	store_name: str
	warehouse: str
	price_list: str
	cost_center: Optional[str] = None
	store_description: Optional[str] = None
	sort_order: Optional[int] = None
	hero_image: Optional[str] = None

	def as_dict(self):
		return asdict(self)


def is_multi_store_enabled() -> bool:
	settings = frappe.get_cached_doc("Webshop Settings")
	return bool(getattr(settings, "enable_multi_store", 0))


def get_published_stores() -> list[StoreContext]:
	rows = frappe.get_all(
		"Website Store",
		fields=[
			"name",
			"slug",
			"store_name",
			"warehouse",
			"price_list",
			"cost_center",
			"store_description",
			"sort_order",
			"hero_image",
		],
		filters={"is_published": 1, "disabled": 0},
		order_by="sort_order asc, store_name asc",
	)
	return [StoreContext(**row) for row in rows]


def get_default_store() -> Optional[StoreContext]:
	settings = frappe.get_cached_doc("Webshop Settings")
	if getattr(settings, "default_website_store", None):
		store = get_store_by_slug(settings.default_website_store)
		if store:
			return store

	stores = get_published_stores()
	return stores[0] if stores else None


def get_store_by_slug(slug: Optional[str]) -> Optional[StoreContext]:
	if not slug:
		return None

	row = frappe.db.get_value(
		"Website Store",
		{"slug": slug, "is_published": 1, "disabled": 0},
		[
			"name",
			"slug",
			"store_name",
			"warehouse",
			"price_list",
			"cost_center",
			"store_description",
			"sort_order",
			"hero_image",
		],
		as_dict=True,
	)
	return StoreContext(**row) if row else None


def get_store_from_cookies() -> Optional[StoreContext]:
	if not is_multi_store_enabled():
		return None

	slug = _get_incoming_cookie("store_slug")
	store = get_store_by_slug(slug)
	if store:
		return store

	default_store = get_default_store()
	if default_store:
		set_store_cookies(default_store)
	return default_store


def set_store_cookies(store: StoreContext) -> None:
	if not hasattr(frappe.local, "cookie_manager"):
		return

	cookie_manager = frappe.local.cookie_manager
	expiry = now_datetime() + timedelta(days=30)

	cookie_manager.set_cookie(
		"store_slug",
		store.slug,
		samesite="Lax",
		expires=expiry,
		max_age=COOKIE_MAX_AGE,
	)
	cookie_manager.set_cookie(
		"store_warehouse",
		store.warehouse,
		samesite="Lax",
		expires=expiry,
		max_age=COOKIE_MAX_AGE,
	)
	cookie_manager.set_cookie(
		"store_price_list",
		store.price_list,
		samesite="Lax",
		expires=expiry,
		max_age=COOKIE_MAX_AGE,
	)


def clear_store_cookies() -> None:
	if hasattr(frappe.local, "cookie_manager"):
		frappe.local.cookie_manager.delete_cookie(list(STORE_COOKIE_KEYS))


def _get_incoming_cookie(key: str) -> Optional[str]:
	if hasattr(frappe.local, "request") and frappe.local.request:
		return frappe.local.request.cookies.get(key)
	return None


def ensure_active_store() -> Optional[StoreContext]:
	store = get_store_from_cookies()
	if store:
		current_cookie_slug = _get_incoming_cookie("store_slug")
		if current_cookie_slug != store.slug:
			set_store_cookies(store)
	return store


def get_active_store_context() -> Optional[dict]:
	store = ensure_active_store()
	return store.as_dict() if store else None
