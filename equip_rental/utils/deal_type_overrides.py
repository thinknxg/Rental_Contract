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
    return target


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    target = core_make_sales_invoice(source_name, target_doc)
    sales_order = frappe.get_doc("Sales Order", source_name)
    target.custom_deal_type = map_deal_type(
        sales_order.custom_deal_type, SALES_ORDER_TO_INVOICE, "Sales Order"
    )
    return target
