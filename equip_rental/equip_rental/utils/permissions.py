import frappe

from equip_rental.utils.common import get_customer_for_user, get_supplier_for_user


def rental_contract_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    if "Rental Manager" in frappe.get_roles(user) or user == "Administrator":
        return True
    customer = get_customer_for_user(user)
    return bool(customer and doc.customer == customer)


def sub_rental_permission(doc, ptype="read", user=None):
    user = user or frappe.session.user
    if "Rental Manager" in frappe.get_roles(user) or user == "Administrator":
        return True
    supplier = get_supplier_for_user(user)
    return bool(supplier and doc.supplier == supplier)


def contract_query_conditions(user):
    user = user or frappe.session.user
    roles = frappe.get_roles(user)
    if user == "Administrator" or "Rental Manager" in roles or "Rental User" in roles:
        return ""
    customer = get_customer_for_user(user)
    if customer:
        return "(`tabRental Contract`.customer = {0})".format(frappe.db.escape(customer))
    return "(1 = 0)"
