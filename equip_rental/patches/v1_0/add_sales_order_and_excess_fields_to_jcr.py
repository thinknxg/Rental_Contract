import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    existing_jcr = {f.fieldname for f in frappe.get_meta("JCR").fields}
    if "sales_order" not in existing_jcr:
        create_custom_fields({"JCR": [{
            "fieldname": "sales_order",
            "label": "Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "hire_order",
        }]}, update=False)

    existing_item = {f.fieldname for f in frappe.get_meta("JCR Item").fields}
    wanted = [
        {
            "fieldname": "sales_order_item",
            "label": "Sales Order Item",
            "fieldtype": "Data",
            "hidden": 1,
            "insert_after": "job_description",
        },
        {
            "fieldname": "contract_days",
            "label": "Contract Days",
            "fieldtype": "Int",
            "insert_after": "custom_dismantle_date",
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
        {
            "fieldname": "excess_amount",
            "label": "Excess Amount",
            "fieldtype": "Currency",
            "options": "currency",
            "read_only": 1,
            "insert_after": "excess_period",
            "in_list_view": 1,
            "columns": 1,
        },
    ]
    fields = [f for f in wanted if f["fieldname"] not in existing_item]
    if fields:
        create_custom_fields({"JCR Item": fields}, update=False)

    frappe.clear_cache(doctype="JCR")
