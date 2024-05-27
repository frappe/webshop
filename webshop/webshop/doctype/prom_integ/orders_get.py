from .prom_client.frappeclient import FrappeClient as ERPClient
from .prom_client.prom_sync import EvoClient as PromClient
import json
from datetime import datetime, timedelta
import frappe
from frappe.utils.password import get_decrypted_password
from frappe.utils import get_host_name
import pytz

ERP_URL = "http://{}".format(get_host_name())
API_KEY = frappe.db.get_value("Prom settings", "Prom settings", "erp_key")
API_SECRET = get_decrypted_password("Prom settings", "Prom settings", "erp_secret")
COMPANY = frappe.db.get_single_value("E Commerce Settings", "company")
conn = ERPClient(ERP_URL, api_key=API_KEY, api_secret=API_SECRET)

AUTH_TOKEN = get_decrypted_password("Prom settings", "Prom settings", "prom_token")
p_client = PromClient(AUTH_TOKEN)
four_days_plus = datetime.now(pytz.timezone('Europe/Kiev')) + timedelta(days=4)

status_mapper = {
    "pending": "To Deliver and Bill",
    "received": "To Deliver and Bill",
    "delivered": "Completed",
    "canceled": "Cancelled",
    "draft": "Draft",
    "paid": "To Deliver"
}

def get_prom_order(limit=100):
    '''
    :param limit: count of orders to return
    :return: list of last prom orders
    '''
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
    return conn.insert(doc=body)


def create_customer(client_info):
    body = {
        'customer_name': client_info['client_full_name'],
        'customer_type': 'Individual',
        'territory': 'Ukraine',
        'customer_details': client_info['comment'],
        'customer_group': 'Individual',
        'doctype': 'Customer'   
    }
    doc = frappe.get_doc(body)
    doc.save()
    return doc


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
    return doc


def customer_exists(client_info, delivery_address, delivery_option):
    client_erp = conn.get_doc("Customer", client_info['client_full_name']).get('name')
    client_contact_erp = conn.get_list(
        "Contact",
        filters=[
            ["Contact Phone", "phone", "in", client_info['phones']]
        ]
        )
    if client_info["emails"]:
        client_email_erp = conn.get_list(
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
    global i
    customer_exists(
        client_info,
        order['delivery_address'],
        order['delivery_option']['name']
        )
    order_time_created = datetime.strptime(order['date_created'], "%Y-%m-%dT%X.%f+00:00")
    print("*"*30, "Customer created?")
    assert frappe.db.exists("Customer", client_info['client_full_name'])
    
    if not order['status'] in status_mapper.keys():
        status_mapper[order['status']] = "On Hold"

    print("*"*10, status_mapper[order['status']], order['status'])
    order_erp = frappe.get_list("Sales Order", filters={'custom_prom_id': order['id']})

    if not order_erp:
        print("#"*50)
        body = {
            'customer': client_info['client_full_name'],
            'transaction_date': order_time_created.strftime("%Y-%m-%d"),
            'custom_prom_id': order['id'],
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
            item_erp = conn.get_list(
                'Website Item',
                filters=[['Website Item', 'item_code', '=', item['sku']]])
            if item_erp:
                item_erp = item_erp[0]
            else:
                frappe.msgprint("Product not found.")
            # item_erp = conn.get_doc('Website Item', item['external_id'])
            if item_erp.get('item_code'):
                item_price = conn.get_doc(
                    'Item Price',
                    filters=[['Item Price', 'item_code', '=', item_erp['item_code']]],
                    fields=['price_list_rate']
                    )
                body['items'].append({
                    'delivery_date': four_days_plus.strftime("%Y-%m-%d"),
                    'item_code': item_erp['item_code'],
                    'qty': int(item['quantity']),
                    'rate': item_price[0]['price_list_rate'],
                    'warehouse': 'All Warehouses - UP',
                    'doctype': 'Sales Order Item'
                })
        order_erp = frappe.get_doc(body)
        # frappe.db.commit()
        # order_erp = frappe.get_doc("Sales Order", temp["name"])
        order_erp.submit()
        order_erp.set_status(True, status_mapper[order['status']])
        order_erp.save()
        from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
        if status_mapper[order['status']] != "On Hold":
            delivery_note = make_delivery_note(order_erp)
            delivery_data = order.get("delivery_provider_data")
            if delivery_data.get("provider") == "nova_poshta":
                delivery_note.shipment_provider="nova_poshta"
                sender_defaults = frappe.get_doc(
                "NovaPoshta",
                "NovaPoshta",
                fields=["pickup_city", "pickup_warehouse", "sender_full_name", "sender_phone"]
                )
                delivery_note.pickup_warehouse = sender_defaults.pickup_warehouse if sender_defaults.pickup_warehouse else ""
                delivery_note.pickup_city = sender_defaults.pickup_city if sender_defaults.pickup_city else ""
                delivery_note.sender_full_name = sender_defaults.sender_full_name if sender_defaults.sender_full_name else ""
                delivery_note.sender_phone = sender_defaults.sender_phone if sender_defaults.sender_phone else ""
                delivery_note.delivery_to_warehouse = delivery_data.get("recipient_warehouse_id")
            delivery_note.save()
        i += 1
        return order_erp
    elif order_erp[0].docstatus == 0:
        order_erp = order_erp[0]
        order_erp.submit()
        order_erp.set_status(True, status_mapper[order['status']])
        order_erp.save()


i = 0
@frappe.whitelist()
def get_all_orders():
    orders = get_prom_order(50)
    orders.reverse()

    for order in orders:
        client_id = order['client_id']
        client_prom = p_client.get_client_by_id(client_id)['client']
        print(client_prom['last_name']+" "+client_prom['first_name'])
        # customer_exists(
        #     client_prom,
        #     order['delivery_address'],
        #     order['delivery_option']['name']
        #     )

        response = create_sales_order(client_prom, order)

@frappe.whitelist()
def check_for_new_orders():
    orders = get_prom_order(10)

    for order in orders:
        status = order.get('status')
        if status == "pending" or status == "received":
            print("*"*30, "Start")
            client_id = order['client_id']
            client_prom = p_client.get_client_by_id(client_id)['client']
            response = create_sales_order(client_prom, order)
            print(response)
    frappe.msgprint(frappe._("{} orders have been added successfully.".format(i)))
    


if __name__ == "__main__":
    get_all_orders()
