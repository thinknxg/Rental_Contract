import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    existing = {f.fieldname for f in frappe.get_meta("Sales Order Item").fields}
    if "custom_contract_days" in existing:
        return
    create_custom_fields({"Sales Order Item": [{
        "fieldname": "custom_contract_days",
        "label": "Contract Days",
        "fieldtype": "Int",
        "insert_after": "contract_days",
        "in_list_view": 1,
        "columns": 1,
        "depends_on": 'eval:["Material Hire Order","Contract Hire Order"].includes(parent.custom_deal_type)',
    }]}, update=False)
    frappe.clear_cache(doctype="Sales Order")
