import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    if frappe.db.exists("Custom Field", "Sales Invoice Item-custom_excess_amount"):
        frappe.delete_doc("Custom Field", "Sales Invoice Item-custom_excess_amount", ignore_permissions=True)

    create_custom_fields({
        "Sales Invoice Item": [{
            "fieldname": "excess_amount",
            "label": "Excess Amount",
            "fieldtype": "Currency",
            "insert_after": "excess_days",
            "in_list_view": 1,
            "columns": 1,
        }]
    })

    frappe.clear_cache(doctype="Sales Invoice Item")
    frappe.db.updatedb("Sales Invoice Item")
