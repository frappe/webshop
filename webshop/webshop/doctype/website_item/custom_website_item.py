import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from erpnext.stock.doctype.item.item import Item

import frappe
from frappe import _
from frappe.utils import cint, cstr, flt, random_string
from frappe.website.doctype.website_slideshow.website_slideshow import get_slideshow
from frappe.website.website_generator import WebsiteGenerator

from webshop.webshop.doctype.item_review.item_review import get_item_reviews
from webshop.webshop.redisearch_utils import (
    delete_item_from_index,
    insert_item_to_index,
    update_index_for_item,
)
from webshop.webshop.shopping_cart.cart import _set_price_list
from webshop.webshop.doctype.override_doctype.item_group import (
    get_parent_item_groups,
    invalidate_cache_for,
)
from erpnext.stock.doctype.item.item import Item
from erpnext.utilities.product import get_price
from webshop.webshop.shopping_cart.cart import get_party
from webshop.webshop.variant_selector.item_variants_cache import (
    ItemVariantsCacheManager,
)
import erpnext
from erpnext.controllers.item_variant import get_variant


class CustomWebSiteItem( ):
    
    @property
    def custom_website_pricing_virtual(self):
        currency = frappe.defaults.get_global_default('currency')
        if self.custom_on_sale:
            if self.custom_on_sale:
                discount_in_percentage = self.custom_set_discount_value if self.custom_select_discount_type_ == 'Discount Percentage' else self.custom_set_discount_value / self.custom_price * 100 if self.custom_price else 0
                discount_in_value = (self.custom_set_discount_value / 100) * self.custom_price if self.custom_select_discount_type_ == 'Discount Percentage' else self.custom_set_discount_value
                custom_sale_price = self.custom_sales_price = (self.custom_price or 0) - (discount_in_value or 0)
        else:
            discount_in_percentage = 0
            discount_in_value = 0
            custom_sale_price = 0
            custom_price = self.custom_price
            
            
        custom_sale_price = float(custom_sale_price) if isinstance(custom_sale_price, str) else custom_sale_price
        custom_sale_price=custom_sale_price if self.custom_on_sale else 0
        # discount_in_percentage = float(discount_in_percentage) if isinstance(discount_in_percentage, str) else discount_in_percentage
        discount_in_value = float(discount_in_value) if isinstance(discount_in_value, str) else discount_in_value


        return f'''
            <div>
                <div class="price-in-item">
                    <span class="price-label-in-item">Price</span>
                    <span>{frappe.utils.fmt_money(self.custom_price, currency=currency)}</span>
                </div>
                {'<div class="sales-price-in-item"><span class="sales-price-label-in-item">Sales Price</span><span>'+frappe.utils.fmt_money(custom_sale_price,currency=currency)+'</span></div>' if custom_sale_price>0 else ""}
                <div class="discount-perc-price-in-item">
                    {f'<span class="discount-price-label-in-item">Discount in %</span><span>{round(discount_in_percentage, 2):g} %</span>' if discount_in_percentage > 0 else ""}
                </div>
                {'<div class="discount-val-price-in-item"><span class="discount-value-label-in-item">Discount in Value</span><span>'+frappe.utils.fmt_money(discount_in_value, currency=currency)+'</span></div>' if discount_in_value>0 else ""}
            </div>
        '''

    def before_save(self):
        if self.is_new():
            if self.item_code:
                item_doc = frappe.get_doc('Item', self.item_code)
                self.custom_price = item_doc.standard_rate
                self.custom_on_sale = item_doc.custom_on_sale
                self.custom_select_discount_type_ = item_doc.custom_discount_type
                self.custom_set_discount_value = item_doc.custom_discount_value
                self.custom_sales_price = item_doc.custom_sale_price_not_virtual
                self.custom_sale_price = item_doc.custom_sale_price_not_virtual
                self.update_price()
                self.update_pricing_rule() 
                
        fields = self.get_changed_fields()
        if fields and len(fields) >= 2:
            if self.custom_price:
                self.update_price()
                self.update_pricing_rule() 
        else:
            pass

     
    def update_pricing_rule(self):
        price_list = frappe.db.get_single_value("Webshop Settings", "price_list") or frappe.db.get_value("Price List", _("Website Selling"))
        existing_rules = frappe.db.exists('Pricing Rule', {'title': self.item_code, 'for_price_list': price_list})

        if existing_rules:
            pricing_rule = frappe.get_doc('Pricing Rule', existing_rules)
            pricing_rule.update({
                'disable': 0 if self.custom_on_sale else 1,
                'rate_or_discount': self.custom_select_discount_type_,
                'rate': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Rate' else 0,
                'discount_amount': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Discount Amount' else 0,
                'discount_percentage': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Discount Percentage' else 0
            })
            # Save the document
            pricing_rule.save()
        else:
            self.add_pricing_rule()

     
    def add_pricing_rule(self):
        price_list = frappe.db.get_single_value("Webshop Settings", "price_list") or frappe.db.get_value("Price List", _("Website Selling"))
        pricing_rule = frappe.get_doc({
            'doctype': 'Pricing Rule',
            'apply_on': "Item Code",
            'price_or_product_discount': "Price",
            'selling': 1,
            'for_price_list': price_list,
            'title': self.item_code,
            'pricing_rule_name': self.item_code,
            'currency': erpnext.get_default_currency(),
            'rate_or_discount': self.custom_select_discount_type_,
            'rate': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Rate' else 0,
            'discount_amount': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Discount Amount' else 0,
            'discount_percentage': self.custom_set_discount_value if self.custom_select_discount_type_ == 'Discount Percentage' else 0,
            'items': [{
                'item_code': self.item_code
            }]
        })
        pricing_rule.insert()
        return pricing_rule 
        
    def update_price(self, price_list=None):
        if self.custom_price:
            if not price_list:
                price_list = frappe.db.get_single_value("Webshop Settings", "price_list") or frappe.db.get_value("Price List", _("Website Selling"))
                    
            existing_price = frappe.db.exists('Item Price', {'item_code': self.item_code,'price_list': price_list})
            if existing_price:
                frappe.db.set_value('Item Price', existing_price, 'price_list_rate', self.custom_price)
            else:
                if price_list:
                    item_price = frappe.get_doc(
                        {
                            "doctype": "Item Price",
                            "price_list": price_list,
                            "item_code": self.item_code,
                            "currency": erpnext.get_default_currency(),
                            "price_list_rate": self.custom_price,
                        }
                    )
                    item_price.insert()
                    self.item_price = item_price    
                
    def get_changed_fields(self):
        changed_fields = []
        initilaized_fields = []
        old_doc = self.get_doc_before_save()
        if not old_doc:
            return []
        for field in frappe.get_meta(self.doctype).fields:
            if not field.is_virtual and field.fieldtype != 'Table':
                if self.get(field.fieldname) != None and old_doc.get(field.fieldname) == None:
                    initilaized_fields.append(field.fieldname)
                
                if self.get(field.fieldname) != old_doc.get(field.fieldname):
                    changed_fields.append(field.fieldname)
                
        return [changed_fields, initilaized_fields]  


@frappe.whitelist() 
def get_item_data_for_web_item(reference,item_name):
    main_item = frappe.get_doc("Item",item_name)
    if( main_item is not None ):
        temp_dict=dict({
            "custom_short_description":main_item.custom_short_description,
            "description":main_item.description,
            "custom_return__refund_title":main_item.custom_return__refund_title,
            "custom_return__refund_description":main_item.custom_return__refund_description,
            "custom_shipping_title":main_item.custom_shipping_title,
            "custom_shipping_description":main_item.custom_shipping_description,
        })
        frappe.response['message'] = temp_dict
    else:
        frappe.response['message'] = "None"

@frappe.whitelist() 
def get_images_from_item(item_code, website_item):
    item = frappe.get_doc("Item", item_code)
    if( item is not None ):
        if website_item:
            website_item = frappe.get_doc("Website Item", website_item)
            if website_item:
                website_item.website_images = []
                for custom_image in item.get("custom_images"):
                    image = frappe.copy_doc(frappe.get_doc("File", custom_image.get("image"))).update({
                        "attached_to_doctype": "Website Item",
                        "attached_to_name": website_item.name,
                        "attached_to_field": "website_images",
                    }).insert()
                    website_item.append("website_images", {
                        "file_url": image.file_url,
                        "image": image.name,
                    })
                website_item.save()
        
        
        
@frappe.whitelist()
def make_website_item(doc, save=True):
    print("custom => make_website_item")
    """
    Make Website Item from Item. Used via Form UI or patch.
    """
    if not doc:
        return
    if isinstance(doc, str):
        doc = json.loads(doc)
    if frappe.db.exists("Website Item", {"item_code": doc.get("item_code")}):
        message = _("Website Item already exists against {0}").format(
            frappe.bold(doc.get("item_code"))
        )
        frappe.throw(message, title=_("Already Published"))
    website_item = frappe.new_doc("Website Item")
    website_item.autoname()
    website_item.web_item_name = doc.get("item_name")
    fields_to_map = [
        "item_code",
        "item_name",
        "item_group",
        "stock_uom",
        "brand",
        "has_variants",
        "variant_of",
        "description",
        "custom_return__refund_title",
        "custom_shipping_title",
        "custom_shipping_description"
    ]
    for field in fields_to_map:
        website_item.update({field: doc.get(field)})
    website_item.short_description=doc.get("custom_short_description")
    website_item.web_long_description=doc.get("description")
    website_item.custom_long_description=doc.get("custom_return__refund_description")
    
    if not frappe.flags.in_migrate and (
        doc.get("image") and not website_item.website_image
    ):
        website_item.website_image = doc.get("image")
    
    for custom_image in doc.get("custom_images", []):
        image = frappe.copy_doc(frappe.get_doc("File", custom_image.get("image"))).update({
            "attached_to_doctype": "Website Item",
            "attached_to_name": website_item.name,
            "attached_to_field": "website_images",
        }).insert()
        website_item.append("website_images", {
            "file_url": image.file_url,
            "image": image.name,
        })
    
    if not save:
        return website_item
    
    website_item.insert(set_name=website_item.name)
    
    if doc.get("has_variants"):
        variants_list = []
        variants = doc.get("custom__item_product_variants")
        if variants:
            for variant in variants:
                variants_list.append({
                    "variant": variant["variant"],
                    "data_hwpc": variant["data_hwpc"],
                    "status": variant["status"]
                })
        website_item.set("custom__item_product_variants", variants_list)
        frappe.enqueue(
            "webshop.webshop.doctype.website_item.custom_website_item.make_website_variants",
            item_code=doc.get("item_code"),
            now=frappe.flags.in_test,
        )
        website_item.save()
        
    insert_item_to_index(website_item)
    return [website_item.name, website_item.web_item_name]


def make_website_variants(item_code):
    variants = frappe.get_all("Item", filters={"variant_of": item_code}, fields=["name", "item_name"])
    for variant in variants:
        doc = frappe.get_doc("Item", variant.name)
        make_website_item(doc)
        # if item_code:
        #     insert_item_pricing(item_code, variant_price=doc.standard_rate)
        
# def insert_item_pricing(item_code, price_list='Standard Selling', variant_price=0.0):
#     existing_prices = frappe.get_all('Item Price', filters={'item_code': item_code}, fields=['name', 'price_list_rate'])
#     if existing_prices:
#         frappe.db.set_value('Item Price', existing_prices[0].name, 'price_list_rate', variant_price)
#         frappe.db.set_value('Website Item', item_code, 'standard_rate', variant_price)
#     else:
#         CustomItem.add_price(item_code, variant_price)
#         frappe.db.set_value('Website Item', item_code, 'standard_rate', variant_price)