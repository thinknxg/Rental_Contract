import frappe
from frappe.model.mapper import get_mapped_doc



def _map_item(source, target, source_parent):
    target.item_code = source.item_code
    target.description = source.description
    target.qty = source.qty
    target.contract_rate = source.rate
    target.contract_days = source.rotation_qty
    target.contract_amount = source.amount


@frappe.whitelist()
def make_hire_order(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.party_name

    return get_mapped_doc(
        "Quotation",
        source_name,
        {
            "Quotation": {
                "doctype": "Hire Order",
                "field_map": {},
                "validation": {"docstatus": ["=", 1]},
            },
            "Quotation Item": {
                "doctype": "Hire Order Item",
                "postprocess": _map_item,
            },
        },
        target_doc,
        set_missing_values,
    )


@frappe.whitelist()
def make_hire_order_contract(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.party_name

    return get_mapped_doc(
        "Quotation",
        source_name,
        {
            "Quotation": {
                "doctype": "Hire Order Contract",
                "field_map": {},
                "validation": {"docstatus": ["=", 1]},
            },
            "Quotation Item": {
                "doctype": "Hire Order Contract Item",
                "postprocess": _map_item,
            },
        },
        target_doc,
        set_missing_values,
    )
