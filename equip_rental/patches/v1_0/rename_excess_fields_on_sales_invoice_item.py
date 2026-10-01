import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    for old_name in ("Sales Invoice Item-custom_excess_charge", "Sales Invoice Item-custom_excess_days"):
        if frappe.db.exists("Custom Field", old_name):
            frappe.delete_doc("Custom Field", old_name, ignore_permissions=True)

    create_custom_fields({
        "Sales Invoice Item": [
            {
                "fieldname": "excess_charge",
                "label": "Excess Charge",
                "fieldtype": "Currency",
                "insert_after": "qty",
                "in_list_view": 1,
                "columns": 1,
            },
            {
                "fieldname": "excess_days",
                "label": "Excess Days",
                "fieldtype": "Float",
                "insert_after": "excess_charge",
                "in_list_view": 1,
                "columns": 1,
            },
        ]
    })

    frappe.clear_cache(doctype="Sales Invoice Item")
    frappe.db.updatedb("Sales Invoice Item")
