from .prom_client.prom_sync import EvoClient as PromClient
import json
from datetime import datetime, timedelta
import frappe
from frappe.utils.password import get_decrypted_password
import pytz

API_KEY = frappe.db.get_value("Prom settings", "Prom settings", "erp_key")
API_SECRET = get_decrypted_password("Prom settings", "Prom settings", "erp_secret")

COMPANY = frappe.db.get_single_value("E Commerce Settings", "company")
CUSTOMER_GROUP = frappe.db.get_single_value("E Commerce Settings", "default_customer_group")
delivery_date = datetime.now(pytz.timezone('Europe/Kiev')) + timedelta(days=4)

AUTH_TOKEN = get_decrypted_password("Prom settings", "Prom settings", "prom_token")
p_client = PromClient(AUTH_TOKEN)

class PromCustomer():
    def __init__(self, client_info) -> None:
        pass
    def map_with_prom(self):
        pass
    def check_erp_existence(self):
        pass
    def create_customer(self):
        pass

class PromOrder():
    def __init__(self) -> None:
        pass

def get_prom_order(limit=100):
    return p_client.get_orders(limit=limit)['orders']


def create_shipping_address(delivery_address, full_name):
    comma_index = delivery_address.find(',')
    body = {
        'address_line1': "Нова пошта" + delivery_address[comma_index+1:],
        'city': delivery_address[:comma_index],
        'country': 'Ukraine',
        'address_type': 'Shipping',
        'links': [{
            'link_name': full_name,
            'link_doctype': 'Customer',
            'doctype': 'Dynamic Link'
        }], 
        'doctype': 'Address'
    }
    shipping_address = frappe.get_doc(body)
    shipping_address.save()


def create_customer(client_info):
    body = {
        'customer_name': client_info['client_full_name'],
        'customer_type': CUSTOMER_GROUP,
        'territory': 'Ukraine',
        'customer_details': client_info['comment'],
        'customer_group': CUSTOMER_GROUP,
        'doctype': 'Customer'   
    }
    customer = frappe.get_doc(body)
    customer.save()


def edit_customer_contact(client_info):
    pass


def create_customer_contact(client_info):
    body = {
        'first_name': client_info['first_name'],
        'last_name': client_info['last_name'],
        'links': [{
            'link_name': client_info['client_full_name'],
            'link_doctype': 'Customer',
            'doctype': 'Dynamic Link'
        }], 
        'doctype': 'Contact'
    }
    phones = []
    emails = []
    for i in client_info['phones']:
        phones.append({
            'doctype': 'Contact Phone',
            'phone': i
        })
    for i in client_info['emails']:
        emails.append({
            'doctype': 'Contact Email',
            'email_id': i
        })
    body['phone_nos'] = phones
    body['email_ids'] = emails
    doc = frappe.get_doc(body)
    doc.save()


def customer_exist(client_info, delivery_address, delivery_option):
    client_erp = frappe.get_doc("Customer", client_info['client_full_name']).get('name')
    client_contact_erp = frappe.get_all(
        "Contact",
        filters=[
            ["Contact Phone", "phone", "in", client_info['phones']]
        ]
        )
    if client_info["emails"]:
        client_email_erp = frappe.get_all(
            "Contact",
            filters=[
                ["Contact Email","email_id","in", client_info["emails"]]
            ])
    else:
        client_email_erp = None

    if client_erp and (client_contact_erp or client_email_erp):
        print("Customer and their contact exists")
    else:
        if not client_erp:
            create_customer(client_info)
        if (not client_contact_erp and client_info['phones']) or \
            (not client_email_erp and client_info["emails"]):
            create_customer_contact(client_info)
            if delivery_option == 'Доставка "Нова Пошта"':
                create_shipping_address(
                    delivery_address,
                    client_info['client_full_name']
                    )


def create_sales_order(client_info, order):
    customer_exist(
        client_info,
        order['delivery_address'],
        order['delivery_option']['name']
        )
    order_time_created = datetime.strptime(order['date_created'], "%Y-%m-%dT%X.%f+00:00")
    body = {
        'customer': client_info['client_full_name'],
        'transaction_date': order_time_created.strftime("%Y-%m-%d"),
        'company': COMPANY,
        'currency': 'UAH',
        'territory': 'Ukraine',
        'order_type': 'Sales',
        'contact_email': order['email'],
        'contact_mobile': order['phone'],
        'conversion_rate': 0.4035,
        'items': [],
        'doctype': 'Sales Order'
    }
    for item in order['products']:
        print(f"{item}")
        item_erp = frappe.get_all(
            'Website Item',
            filters=[['Website Item', 'item_code', '=', item['sku']]])
        if item_erp:
            item_erp = item_erp[0]
        else:
            frappe.msgprint("Product not found.")
        # item_erp = conn.get_doc('Website Item', item['external_id'])
        if item_erp.get('item_code'):
            item_price = frappe.get_all(
                'Item Price',
                filters=[['Item Price', 'item_code', '=', item_erp['item_code']]],
                fields=['price_list_rate']
                )
            body['items'].append({
                'delivery_date': '2023-01-31', 
                'item_code': item_erp['item_code'],
                'qty': int(item['quantity']),
                'rate': item_price[0]['price_list_rate'],
                'warehouse': 'All Warehouses - UP',
                'doctype': 'Sales Order Item'
            })
    doc = frappe.get_doc(body)
    doc.save()

@frappe.whitelist()
def get_all_orders():
    orders = get_prom_order(1)
    for order in orders:
        client_id = order['client_id']
        client_prom = p_client.get_client_by_id(client_id)['client']
        create_sales_order(client_prom, order)

if __name__ == "__main__":
    get_all_orders()
