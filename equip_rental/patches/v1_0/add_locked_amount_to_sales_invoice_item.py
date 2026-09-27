import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Sales Invoice Item": [
            {
                "fieldname": "custom_locked_rate",
                "label": "Locked Rate",
                "fieldtype": "Currency",
                "hidden": 1,
                "no_copy": 1,
                "insert_after": "amount",
            },
            {
                "fieldname": "custom_locked_amount",
                "label": "Locked Amount",
                "fieldtype": "Currency",
                "hidden": 1,
                "no_copy": 1,
                "insert_after": "custom_locked_rate",
            },
        ]
    })
    frappe.clear_cache(doctype="Sales Invoice")
