import frappe
from erpnext.crm.doctype.lead.lead import make_quotation as core_make_quotation
from erpnext.selling.doctype.quotation.quotation import make_sales_order as core_make_sales_order
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice as core_make_sales_invoice

from equip_rental.utils.deal_type_mapping import (
    LEAD_TO_QUOTATION,
    QUOTATION_TO_SALES_ORDER,
    SALES_ORDER_TO_INVOICE,
    map_deal_type,
)


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
    target = core_make_quotation(source_name, target_doc)
    lead = frappe.get_doc("Lead", source_name)
    target.custom_deal_type = map_deal_type(lead.custom_deal_type, LEAD_TO_QUOTATION, "Lead")
    return target


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
    target = core_make_sales_order(source_name, target_doc)
    quotation = frappe.get_doc("Quotation", source_name)
    target.custom_deal_type = map_deal_type(
        quotation.custom_deal_type, QUOTATION_TO_SALES_ORDER, "Quotation"
    )

    if quotation.custom_deal_type in ("Material Hire", "Contract Hire"):
        quotation_items = {row.name: row for row in quotation.items}
        for target_row in target.items:
            source_row = quotation_items.get(target_row.quotation_item)
            if source_row:
                target_row.contract_days = source_row.rotation_qty

    return target


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    target = core_make_sales_invoice(source_name, target_doc)
    sales_order = frappe.get_doc("Sales Order", source_name)
    target.custom_deal_type = map_deal_type(
        sales_order.custom_deal_type, SALES_ORDER_TO_INVOICE, "Sales Order"
    )
    return target


def recalculate_hire_amounts(doc, method=None):
    """Quotation validate() hook: for Material Hire / Contract Hire, amount
    is Qty x Rate x Duration/Rotation, not the standard Qty x Rate.

    Core's calculate_taxes_and_totals() runs earlier in validate() and sums
    the header totals from the WRONG (Qty x Rate) item amounts. So after
    fixing each item's amount here, the header totals must be recomputed
    from scratch too, or they stay stuck at the pre-fix sum.
    """
    hire_types = ("Material Hire", "Contract Hire")
    if doc.custom_deal_type not in hire_types:
        return

    conversion_rate = doc.conversion_rate or 1
    total = 0

    for item in doc.items:
        multiplier = item.rotation_qty if item.rotation_qty else 1
        item.amount = item.qty * item.rate * multiplier
        item.net_amount = item.amount
        item.base_amount = item.amount * conversion_rate
        item.base_net_amount = item.base_amount
        total += item.amount

    doc.total = total
    doc.net_total = total
    doc.base_total = total * conversion_rate
    doc.base_net_total = total * conversion_rate
    doc.grand_total = total
    doc.rounded_total = round(total)
    doc.base_grand_total = total * conversion_rate
    doc.base_rounded_total = round(total * conversion_rate)


def recalculate_hire_amounts_so(doc, method=None):
    """Sales Order validate() hook: for Material Hire Order / Contract Hire
    Order, amount is Qty x Rate x Days (contract_days), not the standard
    Qty x Rate. Mirrors recalculate_hire_amounts() for Quotation -- must
    also redo the header totals since core computes them earlier in
    validate() from the wrong (Qty x Rate) amounts."""
    hire_types = ("Material Hire Order", "Contract Hire Order")
    if doc.custom_deal_type not in hire_types:
        return

    conversion_rate = doc.conversion_rate or 1
    total = 0

    for item in doc.items:
        multiplier = item.contract_days if item.contract_days else 1
        item.amount = item.qty * item.rate * multiplier
        item.net_amount = item.amount
        item.base_amount = item.amount * conversion_rate
        item.base_net_amount = item.base_amount
        total += item.amount

    doc.total = total
    doc.net_total = total
    doc.base_total = total * conversion_rate
    doc.base_net_total = total * conversion_rate
    doc.grand_total = total
    doc.rounded_total = round(total)
    doc.base_grand_total = total * conversion_rate
    doc.base_rounded_total = round(total * conversion_rate)
