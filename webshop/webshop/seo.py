import json
from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import cstr, flt, get_url, strip_html_tags


SITE_NAME = "Euro Plast"
DEFAULT_DESCRIPTION = (
	"Euro Plast offers durable, BPA-free plastic storage, kitchen, bath, "
	"and household products for everyday use in Pakistan."
)


def clean_text(value, limit=None):
	text = " ".join(strip_html_tags(cstr(value or "")).split())
	if limit and len(text) > limit:
		return text[: limit - 1].rsplit(" ", 1)[0] + "…"
	return text


def absolute_url(route_or_path=None):
	path = cstr(route_or_path or "").strip()
	if path.startswith("http://") or path.startswith("https://"):
		return path

	path = "/" + path.lstrip("/")
	if path != "/":
		path = path.rstrip("/")
	return get_url(path)


def image_url(path):
	if not path:
		return None
	return absolute_url(path) if not cstr(path).startswith("data:") else None


def set_page_seo(context, title, description=None, route=None, image=None, og_type="website"):
	title = clean_text(title, 70) or SITE_NAME
	description = clean_text(description, 160) or DEFAULT_DESCRIPTION
	request = getattr(frappe.local, "request", None)
	canonical_url = absolute_url(route or getattr(context, "route", None) or getattr(request, "path", "/"))
	image = image_url(image)

	context.title = title
	context.canonical_url = canonical_url
	context.metatags = frappe._dict(context.get("metatags") or {})
	context.metatags.title = title
	context.metatags.description = description
	context.metatags.url = canonical_url
	context.metatags["og:type"] = og_type
	context.metatags["og:site_name"] = SITE_NAME
	context.metatags["og:title"] = title
	context.metatags["og:description"] = description
	context.metatags["twitter:title"] = title
	context.metatags["twitter:description"] = description

	if image:
		context.metatags.image = image
		context.metatags["og:image"] = image
		context.metatags["twitter:image"] = image
		context.metatags["twitter:card"] = "summary_large_image"
	else:
		context.metatags["twitter:card"] = "summary"

	return context


def add_json_ld(context, *schemas):
	items = [schema for schema in schemas if schema]
	if not items:
		return

	existing = list(context.get("seo_json_ld") or [])
	existing.extend(items)
	context.seo_json_ld = existing
	context.seo_json_ld_json = json.dumps(existing if len(existing) > 1 else existing[0], ensure_ascii=False)


def organization_schema():
	return {
		"@context": "https://schema.org",
		"@type": "Organization",
		"name": SITE_NAME,
		"url": absolute_url("/"),
		"logo": absolute_url("/files/e3.png"),
		"sameAs": [],
	}


def website_schema():
	return {
		"@context": "https://schema.org",
		"@type": "WebSite",
		"name": SITE_NAME,
		"url": absolute_url("/"),
		"potentialAction": {
			"@type": "SearchAction",
			"target": absolute_url("/product_search?search={search_term_string}"),
			"query-input": "required name=search_term_string",
		},
	}


def breadcrumb_schema(parents, current_name, current_route):
	items = []
	for idx, parent in enumerate(parents or [], start=1):
		items.append({
			"@type": "ListItem",
			"position": idx,
			"name": clean_text(parent.get("name")),
			"item": absolute_url(parent.get("route")),
		})

	items.append({
		"@type": "ListItem",
		"position": len(items) + 1,
		"name": clean_text(current_name),
		"item": absolute_url(current_route),
	})

	return {
		"@context": "https://schema.org",
		"@type": "BreadcrumbList",
		"itemListElement": items,
	}


def product_schema(doc, context):
	description = clean_text(doc.get("web_long_description") or doc.get("description"), 500)
	product = {
		"@context": "https://schema.org",
		"@type": "Product",
		"name": clean_text(doc.get("web_item_name") or doc.get("item_name") or doc.get("item_code")),
		"sku": doc.get("item_code"),
		"category": doc.get("item_group"),
		"description": description or DEFAULT_DESCRIPTION,
		"url": absolute_url(doc.get("route")),
		"brand": {"@type": "Brand", "name": SITE_NAME},
	}

	if doc.get("website_image"):
		product["image"] = [image_url(doc.get("website_image"))]

	price = ((context.get("shopping_cart") or {}).get("product_info") or {}).get("price") or {}
	if price.get("price_list_rate"):
		product["offers"] = {
			"@type": "Offer",
			"url": absolute_url(doc.get("route")),
			"price": flt(price.get("price_list_rate")),
			"priceCurrency": price.get("currency") or "PKR",
			"availability": "https://schema.org/InStock",
			"itemCondition": "https://schema.org/NewCondition",
		}

		product_info = (context.get("shopping_cart") or {}).get("product_info") or {}
		if product_info.get("on_backorder"):
			product["offers"]["availability"] = "https://schema.org/PreOrder"
		elif product_info.get("in_stock") == 0:
			product["offers"]["availability"] = "https://schema.org/OutOfStock"

	return product


def collection_schema(title, description, route):
	return {
		"@context": "https://schema.org",
		"@type": "CollectionPage",
		"name": clean_text(title),
		"description": clean_text(description, 300) or DEFAULT_DESCRIPTION,
		"url": absolute_url(route),
		"isPartOf": website_schema(),
	}
