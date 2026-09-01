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
        "Cross Hire Order",
        filters={"supplier": supplier, "docstatus": 1},
        fields=["name", "from_date", "expected_to_date", "status",
                "estimated_total_cost", "currency", "vendor_reference"],
        order_by="from_date desc", limit_page_length=50)

    for order in context.orders:
        order.items = frappe.get_all(
            "Cross Hire Order Item", filters={"parent": order.name},
            fields=["description", "vendor_plant_no", "rate_basis", "rate",
                    "on_hire_date", "expected_off_hire_date", "actual_off_hire_date",
                    "item_status", "expected_amount"])

    context.equipment = frappe.get_all(
        "Rental Equipment",
        filters={"supplier": supplier, "ownership": "Cross-Hired"},
        fields=["name", "equipment_name", "equipment_category", "status",
                "current_location"],
        order_by="equipment_name asc")
    return context
