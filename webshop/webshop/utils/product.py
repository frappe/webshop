import frappe
from frappe.utils import getdate, nowdate

from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.doctype.warehouse.warehouse import get_child_warehouses
from frappe.utils import flt


def get_web_item_qty_in_stock(item_code, item_warehouse_field, warehouse=None):
	in_stock, total_stock = 0, 0.0

	template_item_code, is_stock_item = frappe.db.get_value(
		"Item", item_code, ["variant_of", "is_stock_item"]
	)

	# أول محاولة للحصول على المخزن من Website Item
	if not warehouse:
		warehouse = frappe.db.get_value("Website Item", {"item_code": item_code}, item_warehouse_field)

	# إذا ما زال لا يوجد مخزن، جرّب الصنف القالب
	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value("Website Item", {"item_code": template_item_code}, item_warehouse_field)

	# معالجة حالة المخزن
	if warehouse:
		if frappe.get_cached_value("Warehouse", warehouse, "is_group"):
			warehouses = get_child_warehouses(warehouse)
		else:
			warehouses = [warehouse]
	else:
		# إذا لا يوجد مخزن، خذ كل المخازن التي ليست مجموعة
		warehouses = frappe.db.get_all("Warehouse", filters={"is_group": 0}, pluck="name")

	# جمع الكميات
	for wh in warehouses:
		stock_qty = frappe.db.sql(
			"""
			SELECT S.actual_qty / IFNULL(C.conversion_factor, 1)
			FROM tabBin S
			INNER JOIN `tabItem` I ON S.item_code = I.item_code
			LEFT JOIN `tabUOM Conversion Detail` C
				ON I.sales_uom = C.uom AND C.parent = I.item_code
			WHERE S.item_code = %s AND S.warehouse = %s
			""",
			(item_code, wh),
		)

		if stock_qty and stock_qty[0][0] is not None:
			qty = flt(stock_qty[0][0])
			total_stock += adjust_qty_for_expired_items(item_code, qty, wh)

	in_stock = 1 if total_stock > 0 else 0

	return frappe._dict({
		"in_stock": in_stock,
		"stock_qty": total_stock,
		"is_stock_item": is_stock_item
	})



def adjust_qty_for_expired_items(item_code, stock_qty, warehouse):
	# تحويل stock_qty إلى قيمة عددية موحدة
	if isinstance(stock_qty, (int, float)):
		stock_qty_value = stock_qty
	elif isinstance(stock_qty, list):
		# مثال: [[10.0]] → 10.0
		stock_qty_value = stock_qty[0][0] if stock_qty and stock_qty[0] else 0
	else:
		stock_qty_value = 0

	# استعلام الدُفعات وانتهاء الصلاحية
	batches = frappe.get_all("Batch", filters=[{"item": item_code}], fields=["expiry_date", "name"])
	expired_batches = get_expired_batches(batches)

	for batch in expired_batches:
		if warehouse:
			stock_qty_value = max(0, stock_qty_value - get_batch_qty(batch, warehouse))
		else:
			stock_qty_value = max(0, stock_qty_value - qty_from_all_warehouses(get_batch_qty(batch)))

		if not stock_qty_value:
			break

	return stock_qty_value



def get_expired_batches(batches):
	"""
	:param batches: A list of dict in the form [{'expiry_date': datetime.date(20XX, 1, 1), 'name': 'batch_id'}, ...]
	"""
	return [b.name for b in batches if b.expiry_date and b.expiry_date <= getdate(nowdate())]


def qty_from_all_warehouses(batch_info):
	"""
	:param batch_info: A list of dict in the form [{u'warehouse': u'Stores - I', u'qty': 0.8}, ...]
	"""
	qty = 0
	for batch in batch_info:
		qty = qty + batch.qty

	return qty


def get_non_stock_item_status(item_code, item_warehouse_field):
	# if item is a product bundle, check if its bundle items are in stock
	if frappe.db.exists("Product Bundle", item_code):
		items = frappe.get_doc("Product Bundle", item_code).get_all_children()
		bundle_warehouse = frappe.db.get_value(
			"Website Item", {"item_code": item_code}, item_warehouse_field
		)
		return all(
			get_web_item_qty_in_stock(d.item_code, item_warehouse_field, bundle_warehouse).in_stock
			for d in items
		)
	else:
		return 1
