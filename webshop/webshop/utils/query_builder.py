import frappe
from pypika import Field, Criterion
from pypika import functions as fn
from typing import Any
from frappe.query_builder import DocType

# misc. utils
def is_empty(val):
	return val in (None, "", [], {}, ())


def merge_dicts(primary, secondary):
	result = {}

	keys = set(primary.keys()) | set(secondary.keys())

	for key in keys:
		v1 = primary.get(key)
		v2 = secondary.get(key)

		# Both are dicts → recurse
		if isinstance(v1, dict) and isinstance(v2, dict):
			result[key] = merge_dicts(v1, v2)

		# Prefer non-empty
		elif is_empty(v1) and not is_empty(v2):
			result[key] = v2
		elif not is_empty(v1) and is_empty(v2):
			result[key] = v1

		# Both non-empty → priority to primary
		else:
			result[key] = v1 if not is_empty(v1) else v2

	return result
# list_item helper code

# Tables
website_item = DocType("Website Item")
item_table = DocType("Website Item Table")  # junction for both
website_category = DocType("Website Category")
website_collection = DocType("Website Collection")

# Aliases for the two junction joins (same table, different roles)
col_junc = item_table.as_("col_junc")  # collection join
cat_junc = item_table.as_("cat_junc")  # category join

# Mapping of API filter keys to database columns for ordering
order_col_map = {
	"created_at": website_item.creation,
	"updated_at": website_item.modified,
	"ranking": website_item.ranking,
	"title": website_item.web_item_name,
	"name": website_item.name,
}

# OperatorMap
def apply_operator_map(field: Field, value: Any) -> Criterion | None:
	if not isinstance(value, dict):
		if isinstance(value, list):
			return field.isin(value)
		return field == value

	op_map = {
		"$eq": lambda f, v: f == v,
		"$ne": lambda f, v: f != v,
		"$in": lambda f, v: f.isin(v),
		"$nin": lambda f, v: f.notin(v),
		"$gt": lambda f, v: f > v,
		"$gte": lambda f, v: f >= v,
		"$lt": lambda f, v: f < v,
		"$lte": lambda f, v: f <= v,
		"$like": lambda f, v: f.like(v),
		"$ilike": lambda f, v: f.like(v),
		"$exists": lambda f, v: (f.notnull() if v else f.isnull()),
	}

	criterion = None
	for op, val in value.items():
		if op in op_map:
			c = op_map[op](field, val)
			criterion = c if criterion is None else criterion & c
	return criterion


def _get_category_with_descendants(category_names: list[str]) -> list[str]:
	"""
	Given a list of category names, returns them plus all their descendants
	using the nested set lft/rgt bounds.

	e.g. "Wearables" might return ["Wearables", "T-Shirts", "Hats", ...]
	"""
	if not category_names:
		return []

	bounds = (
		frappe.qb.from_(website_category)
		.select(website_category.lft, website_category.rgt)
		.where(website_category.name.isin(category_names))
	).run(as_dict=True)

	if not bounds:
		return []

	range_criterion = None
	for bound in bounds:
		c = (website_category.lft >= bound["lft"]) & (
			website_category.rgt <= bound["rgt"]
		)
		range_criterion = c if range_criterion is None else range_criterion | c

	descendants = (
		frappe.qb.from_(website_category)
		.select(website_category.name)
		.where(range_criterion)
	).run(as_dict=True)

	return [d["name"] for d in descendants]


def _junction_subquery(ids: list, parenttype: str) -> object:
	"""
	Returns a subquery that fetches website_item values from the
	junction table for a given parenttype (Collection or Category).
	"""
	return (
		frappe.qb.from_(item_table)
		.select(item_table.website_item)
		.where(item_table.parent.isin(ids))
		.where(item_table.parenttype == parenttype)
		.where(item_table.parentfield == "website_items")
		# no correlated ref needed — the outer IN handles the join
	)


# Recursive filter builder
def build_criterion(filters: dict) -> Criterion | None:
	parts = []

	# $and / $or (recursive)
	if "$and" in filters:
		sub = [build_criterion(f) for f in filters["$and"]]
		sub = [s for s in sub if s is not None]
		if sub:
			c = sub[0]
			for s in sub[1:]:
				c = c & s
			parts.append(c)

	if "$or" in filters:
		sub = [build_criterion(f) for f in filters["$or"]]
		sub = [s for s in sub if s is not None]
		if sub:
			c = sub[0]
			for s in sub[1:]:
				c = c | s
			parts.append(c)

	# Full-text search (q)
	# searches: web_item_name, item_code, short_description
	if "q" in filters:
		q = f"%{filters['q']}%"
		parts.append(
			website_item.web_item_name.like(q)
			| website_item.item_code.like(q)
			| website_item.short_description.like(q)
		)

	# id (maps to `name` in Frappe)
	if "id" in filters:
		c = apply_operator_map(website_item.name, filters["id"])
		if c:
			parts.append(c)

	# item_code
	if "item_code" in filters:
		c = apply_operator_map(website_item.item_code, filters["item_code"])
		if c:
			parts.append(c)

	# handle (maps to `route`)
	if "handle" in filters:
		c = apply_operator_map(website_item.route, filters["handle"])
		if c:
			parts.append(c)

	# title (maps to `web_item_name`)
	if "title" in filters:
		c = apply_operator_map(website_item.web_item_name, filters["title"])
		if c:
			parts.append(c)

	# published / status
	# accepts either bool/int (True/1) or medusa-style "published"/"draft"
	if "published" in filters:
		val = filters["published"]
		if isinstance(val, str):
			val = 1 if val == "published" else 0
		parts.append(website_item.published == int(val))

	if "status" in filters:
		val = filters["status"]
		if isinstance(val, str):
			val = 1 if val == "published" else 0
		parts.append(website_item.published == int(val))

	# brand
	if "brand" in filters:
		c = apply_operator_map(website_item.brand, filters["brand"])
		if c:
			parts.append(c)

	# item_group
	if "item_group" in filters:
		c = apply_operator_map(website_item.item_group, filters["item_group"])
		if c:
			parts.append(c)

	# variant_of
	if "variant_of" in filters:
		c = apply_operator_map(website_item.variant_of, filters["variant_of"])
		if c:
			parts.append(c)

	# has_variants
	if "has_variants" in filters:
		parts.append(website_item.has_variants == int(filters["has_variants"]))

	# created_at / updated_at
	for key, col in [
		("created_at", website_item.creation),
		("updated_at", website_item.modified),
	]:
		if key in filters:
			c = apply_operator_map(col, filters[key])
			if c:
				parts.append(c)

	# collection
	# filters["collection"] = "Best Sellers" | ["Best Sellers", "Summer Sale"]
	if "collection" in filters:
		val = filters["collection"]
		ids = val if isinstance(val, list) else [val]
		parts.append(
			website_item.name.isin(_junction_subquery(ids, "Website Collection"))
		)

	# category
	# filters["category"] = "T-Shirts"
	# filters["category"] = ["T-Shirts", "Wearables"]
	# filters["category"] = {"id": "T-Shirts", "subtree": True}
	# filters["category"] = {"id": ["T-Shirts", "Wearables"], "subtree": True}

	if "category" in filters:
		val = filters["category"]

		# normalise all shapes into ids + subtree flag
		if isinstance(val, dict):
			ids = val["id"] if isinstance(val["id"], list) else [val["id"]]
			subtree = val.get("subtree", False)
		else:
			ids = val if isinstance(val, list) else [val]
			subtree = False

		if subtree:
			ids = _get_category_with_descendants(ids)

		if ids:
			parts.append(
				website_item.name.isin(_junction_subquery(ids, "Website Category"))
			)

	# Combine everything with AND
	if not parts:
		return None
	result = parts[0]
	for p in parts[1:]:
		result = result & p
	return result
