"""
Centralized customer creation service for webshop.
Provides idempotent customer creation with distributed locking to prevent duplicates.
"""

import frappe
import time
from frappe import _
from frappe.contacts.doctype.contact.contact import get_contact_name
from frappe.utils import get_fullname
from frappe.utils.nestedset import get_root_of

from webshop.webshop.doctype.webshop_settings.webshop_settings import (
    get_shopping_cart_settings,
)

logger = frappe.logger("webshop")


def get_or_create_customer_for_user(user=None, cart_settings=None):
    """
    Idempotent customer creation for website users.

    Args:
        user (str): Email address of user (default: current session user)
        cart_settings (WebshopSettings): Optional cart settings document

    Returns:
        Customer document or None if user is not a website user or not a customer role
    """
    if not user:
        user = frappe.session.user

    if frappe.db.get_value("User", user, "user_type") != "Website User":
        return None

    # Check if user should be a customer based on Portal Settings
    portal_settings = frappe.get_single("Portal Settings")
    if portal_settings.default_role != "Customer":
        # User is not configured to be a customer
        return None

    user_roles = frappe.get_roles(user)
    if portal_settings.default_role not in user_roles:
        # User doesn't have customer role
        return None

    # Acquire distributed lock for this user
    lock_key = f"customer_creation_lock:{user}"
    if not _acquire_lock(lock_key):
        # Wait and retry once, then check if customer was created by another process
        time.sleep(0.5)
        customer = get_customer_for_user(user)
        if customer:
            return customer
        # If still no customer after waiting, try one more time
        time.sleep(0.5)
        if not _acquire_lock(lock_key):
            # Could not acquire lock, log and return None to avoid blocking
            frappe.log_error(
                f"Could not acquire lock for customer creation for user {user}",
                "Customer Creation Lock Error"
            )
            return None

    try:
        # Double-check pattern: after acquiring lock, check if customer already exists
        customer = get_customer_for_user(user)
        if customer:
            logger.info(f"Customer already exists for user {user}: {customer.name}")
            return customer

        # Create customer with contact
        logger.info(f"Creating new customer for user {user}")
        customer = _create_customer_with_contact(user, cart_settings)
        logger.info(f"Customer created: {customer.name} for user {user}")
        return customer
    finally:
        # Release lock
        _release_lock(lock_key)


def get_customer_for_user(user):
    """
    Find existing customer linked to user's contact.

    Returns:
        Customer document or None
    """
    contact_name = get_contact_name(user)
    if not contact_name:
        return None

    try:
        contact = frappe.get_doc("Contact", contact_name)
    except frappe.DoesNotExistError:
        return None

    # Find customer link in contact
    for link in contact.links:
        if link.link_doctype == "Customer":
            try:
                return frappe.get_doc("Customer", link.link_name)
            except frappe.DoesNotExistError:
                continue

    return None


def _create_customer_with_contact(user, cart_settings=None):
    """
    Internal function to create customer and link contact.
    Assumes lock is held and customer doesn't already exist.
    """
    if not cart_settings:
        cart_settings = get_shopping_cart_settings()

    fullname = get_fullname(user)

    # Create customer document
    customer = frappe.new_doc("Customer")
    customer.update({
        "customer_name": fullname,
        "customer_type": "Individual",
        "customer_group": cart_settings.default_customer_group,
        "territory": get_root_of("Territory"),
    })

    # Add portal user
    customer.append("portal_users", {"user": user})

    # Add debtors account if checkout enabled
    if cart_settings.enable_checkout:
        from webshop.webshop.shopping_cart.cart import get_debtors_account
        debtors_account = get_debtors_account(cart_settings)
        if debtors_account:
            customer.update({
                "accounts": [{
                    "company": cart_settings.company,
                    "account": debtors_account
                }]
            })

    customer.flags.ignore_mandatory = True
    customer.insert(ignore_permissions=True)

    # Get or create contact and link to customer
    contact = _get_or_create_contact_for_user(user, customer.name)

    # Set as primary contact if contact was created/linked
    if contact and not customer.customer_primary_contact:
        customer.db_set("customer_primary_contact", contact.name)

    return customer


def _get_or_create_contact_for_user(user, customer_name):
    """
    Get existing contact for user or create new one, linking to customer.
    Returns Contact document or None.
    """
    contact_name = get_contact_name(user)

    if contact_name:
        # Contact exists, link it to customer
        try:
            contact = frappe.get_doc("Contact", contact_name)
            link_exists = False
            for link in contact.links:
                if link.link_doctype == "Customer" and link.link_name == customer_name:
                    link_exists = True
                    break

            if not link_exists:
                contact.append("links", {
                    "link_doctype": "Customer",
                    "link_name": customer_name
                })
                contact.flags.ignore_mandatory = True
                contact.save(ignore_permissions=True)

            return contact
        except frappe.DoesNotExistError:
            # Contact disappeared between check and get, fall through to create
            pass

    # Create new contact
    fullname = get_fullname(user)
    contact = frappe.new_doc("Contact")
    contact.update({
        "first_name": fullname,
        "email_ids": [{"email_id": user, "is_primary": 1}]
    })
    contact.append("links", {
        "link_doctype": "Customer",
        "link_name": customer_name
    })
    contact.flags.ignore_mandatory = True
    contact.insert(ignore_permissions=True)

    return contact


def _acquire_lock(lock_key, timeout=30):
    """
    Acquire distributed lock using frappe.cache().

    Returns:
        bool: True if lock acquired, False otherwise
    """
    try:
        # nx=True means set only if not exists, ex=timeout sets expiry in seconds
        return frappe.cache().set(lock_key, "1", ex=timeout, nx=True)
    except Exception:
        # If cache doesn't support nx parameter, fall back to simpler locking
        # This is less safe but better than nothing
        try:
            if frappe.cache().get(lock_key):
                return False
            frappe.cache().set(lock_key, "1", ex=timeout)
            return True
        except Exception:
            # Last resort: log and proceed without locking
            frappe.log_error(
                f"Cache locking failed for key {lock_key}",
                "Customer Service Lock Error"
            )
            return True  # Proceed anyway to avoid blocking


def _release_lock(lock_key):
    """
    Release distributed lock.
    """
    try:
        frappe.cache().delete(lock_key)
    except Exception:
        pass