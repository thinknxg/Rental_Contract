import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    existing = {f.fieldname for f in frappe.get_meta("Quotation Item").fields}
    wanted = [
        {
            "fieldname": "contract_days",
            "label": "Contract Days",
            "fieldtype": "Int",
            "insert_after": "period",
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
        },
        {
            "fieldname": "excess_period",
            "label": "Excess Period",
            "fieldtype": "Select",
            "options": "Days\nWeekly\nMonthly",
            "insert_after": "excess_charge",
            "in_list_view": 1,
            "columns": 1,
        },
    ]
    fields = [f for f in wanted if f["fieldname"] not in existing]
    if fields:
        create_custom_fields({"Quotation Item": fields}, update=False)
    frappe.clear_cache(doctype="Quotation")
