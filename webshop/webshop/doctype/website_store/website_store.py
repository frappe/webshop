# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU General Public License v3. See license.txt

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr


class WebsiteStore(Document):
	def validate(self):
		self._normalize_slug()
		self._validate_slug_format()
		self._validate_company_alignment()
		self._validate_price_list_configuration()

	def _normalize_slug(self) -> None:
		if self.slug:
			self.slug = cstr(self.slug).strip().lower()

		if not self.slug:
			frappe.throw(_("Store slug is required."), title=_("Missing Value"))

	def _validate_slug_format(self) -> None:
		if not re.match(r"^[a-z0-9][a-z0-9\-._]*$", self.slug or ""):
			frappe.throw(
				_("Slug can only include lowercase letters, numbers, hyphen, dot, or underscore."),
				title=_("Invalid Slug"),
			)

		existing = frappe.db.get_value(
			"Website Store",
			{"slug": self.slug, "name": ("!=", self.name or "")},
		)
		if existing:
			frappe.throw(_("Slug already exists. Please choose a unique slug."), title=_("Duplicate Slug"))

	def _validate_company_alignment(self) -> None:
		warehouse_company = frappe.db.get_value("Warehouse", self.warehouse, "company")
		if not warehouse_company:
			return

		settings = frappe.get_cached_doc("Webshop Settings")
		if settings.company and warehouse_company != settings.company:
			frappe.throw(
				_("Warehouse {0} must belong to the Webshop company {1}.").format(
					frappe.bold(self.warehouse), frappe.bold(settings.company)
				),
				title=_("Company Mismatch"),
			)

	def _validate_price_list_configuration(self) -> None:
		price_list_details = frappe.db.get_value(
			"Price List",
			self.price_list,
			["selling", "currency"],
			as_dict=True,
		)
		if not price_list_details:
			frappe.throw(_("Price List {0} does not exist.").format(frappe.bold(self.price_list)))

		if not price_list_details.selling:
			frappe.throw(
				_("Price List {0} must be marked as a Selling Price List.").format(frappe.bold(self.price_list)),
				title=_("Invalid Price List"),
			)

		settings = frappe.get_cached_doc("Webshop Settings")
		if settings.price_list:
			default_currency = frappe.db.get_value(
				"Price List",
				settings.price_list,
				"currency",
			)
			if default_currency and price_list_details.currency != default_currency:
				frappe.throw(
					_("Store price list currency {0} must match the default Webshop currency {1}.").format(
						frappe.bold(price_list_details.currency or _("Unknown")),
						frappe.bold(default_currency),
					),
					title=_("Currency Mismatch"),
				)
