import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    existing = {f.fieldname for f in frappe.get_meta("Sales Order Item").fields}
    hire_depends_on = 'eval:["Material Hire Order","Contract Hire Order"].includes(parent.custom_deal_type)'
    wanted = [
        {
            "fieldname": "contract_days",
            "label": "Contract Days",
            "fieldtype": "Int",
            "insert_after": "uom",
            "in_list_view": 1,
            "columns": 1,
        },
        {
            "fieldname": "excess_charge",
            "label": "Excess Charge",
            "fieldtype": "Currency",
            "options": "currency",
            "insert_after": "contract_days",
            "in_list_view": 1,
            "columns": 2,
            "depends_on": hire_depends_on,
        },
        {
            "fieldname": "excess_period",
            "label": "Excess Period",
            "fieldtype": "Select",
            "options": "Days\nWeekly\nMonthly",
            "insert_after": "excess_charge",
            "in_list_view": 1,
            "columns": 1,
            "depends_on": hire_depends_on,
        },
    ]
    fields = [f for f in wanted if f["fieldname"] not in existing]
    if fields:
        create_custom_fields({"Sales Order Item": fields}, update=False)
    frappe.clear_cache(doctype="Sales Order")
