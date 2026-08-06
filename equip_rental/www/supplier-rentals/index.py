import frappe

from equip_rental.utils.common import get_supplier_for_user

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/supplier-rentals"
        raise frappe.Redirect

    supplier = get_supplier_for_user()
    context.supplier = supplier
    context.title = "Sub-Rental Orders"
    context.no_cache = 1

    if not supplier:
        context.orders = []
        context.equipment = []
        return context

    context.orders = frappe.get_all(
        "Sub Rental Order",
        filters={"supplier": supplier, "docstatus": ["<", 2]},
        fields=["name", "from_date", "to_date", "status", "total_amount", "currency",
                "purchase_invoice"],
        order_by="from_date desc", limit_page_length=50)

    for order in context.orders:
        order.items = frappe.get_all(
            "Sub Rental Order Item", filters={"parent": order.name},
            fields=["equipment", "description", "qty", "rate_basis", "units", "rate",
                    "amount"])

    context.equipment = frappe.get_all(
        "Rental Equipment",
        filters={"supplier": supplier, "ownership": "Sub-Rented"},
        fields=["name", "equipment_name", "equipment_category", "status",
                "current_location"],
        order_by="equipment_name asc")
    return context
