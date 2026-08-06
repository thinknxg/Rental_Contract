import frappe

from equip_rental.utils.common import get_customer_for_user

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-rentals"
        raise frappe.Redirect

    customer = get_customer_for_user()
    context.customer = customer
    context.no_cache = 1
    context.title = "My Rentals"

    if not customer:
        context.contracts = []
        context.invoices = []
        return context

    context.contracts = frappe.get_all(
        "Rental Contract",
        filters={"customer": customer, "docstatus": 1},
        fields=["name", "start_date", "expected_end_date", "actual_end_date", "status",
                "billing_cycle", "estimated_total", "total_billed", "currency"],
        order_by="start_date desc", limit_page_length=50)

    for contract in context.contracts:
        contract.items = frappe.get_all(
            "Rental Contract Item", filters={"parent": contract.name},
            fields=["equipment", "equipment_name", "rate_basis", "rate", "item_status",
                    "charge_from", "off_rent_date"])

    context.invoices = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer, "docstatus": 1,
                 "rental_contract": ["is", "set"]},
        fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount",
                "status", "currency", "rental_contract"],
        order_by="posting_date desc", limit_page_length=50)

    settings = frappe.get_cached_doc("Equipment Rental Settings")
    context.allow_off_hire = settings.allow_portal_off_hire
    return context
