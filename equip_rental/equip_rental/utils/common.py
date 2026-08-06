import frappe
from frappe import _
from frappe.utils import getdate


def get_settings():
    return frappe.get_cached_doc("Equipment Rental Settings")


def default_company():
    settings = get_settings()
    return settings.default_company or frappe.defaults.get_user_default("Company")


def equipment_thumbnail(equipment):
    """Jinja helper - safe image url for an equipment record."""
    image = frappe.db.get_value("Rental Equipment", equipment, "image")
    return image or "/assets/equip_rental/images/equipment-placeholder.svg"


def overlaps(start_a, end_a, start_b, end_b):
    """Inclusive date-range overlap test. Open ends are treated as infinite."""
    start_a, start_b = getdate(start_a), getdate(start_b)
    end_a = getdate(end_a) if end_a else None
    end_b = getdate(end_b) if end_b else None
    if end_a and end_a < start_b:
        return False
    if end_b and end_b < start_a:
        return False
    return True


def get_billing_item(equipment_doc=None, category=None):
    """Resolve the ERPNext Item used for invoicing a piece of equipment."""
    if equipment_doc and equipment_doc.get("item"):
        return equipment_doc.item
    category = category or (equipment_doc.equipment_category if equipment_doc else None)
    if category:
        item = frappe.db.get_value("Equipment Category", category, "default_item")
        if item:
            return item
    frappe.throw(_("Set a Billing Item on the equipment or on its Equipment Category"))


def get_customer_for_user(user=None):
    user = user or frappe.session.user
    contact = frappe.db.get_value("Contact Email", {"email_id": user}, "parent")
    if contact:
        link = frappe.db.get_value(
            "Dynamic Link",
            {"parent": contact, "parenttype": "Contact", "link_doctype": "Customer"},
            "link_name")
        if link:
            return link
    return frappe.db.get_value("Customer", {"portal_users": user}, "name")


def get_supplier_for_user(user=None):
    user = user or frappe.session.user
    contact = frappe.db.get_value("Contact Email", {"email_id": user}, "parent")
    if contact:
        return frappe.db.get_value(
            "Dynamic Link",
            {"parent": contact, "parenttype": "Contact", "link_doctype": "Supplier"},
            "link_name")
    return None
