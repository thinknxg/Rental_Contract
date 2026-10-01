import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    # Clean up earlier partial attempts
    for old in (
        "custom_excess_charge", "custom_excess_days", "custom_excess_amount",
        "custom_base_amount", "excess_charge", "excess_days",
        "excess_period", "excess_amount",
    ):
        name = f"Sales Invoice Item-{old}"
        if frappe.db.exists("Custom Field", name):
            frappe.delete_doc("Custom Field", name, ignore_permissions=True)

    create_custom_fields({
        "Sales Invoice Item": [
            {"fieldname": "excess_charge", "label": "Excess Charge", "fieldtype": "Currency",
             "insert_after": "qty", "in_list_view": 1, "columns": 1},
            {"fieldname": "excess_days", "label": "Excess Days", "fieldtype": "Float",
             "insert_after": "excess_charge", "in_list_view": 1, "columns": 1},
            {"fieldname": "excess_period", "label": "Excess Period", "fieldtype": "Select",
             "options": "Days\nWeekly\nMonthly",
             "insert_after": "excess_days", "in_list_view": 1, "columns": 1},
            {"fieldname": "excess_amount", "label": "Excess Amount", "fieldtype": "Currency",
             "insert_after": "excess_period", "in_list_view": 1, "columns": 1},
        ]
    })

    frappe.clear_cache(doctype="Sales Invoice Item")
