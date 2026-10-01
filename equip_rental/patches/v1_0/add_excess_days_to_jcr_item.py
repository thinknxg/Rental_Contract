import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "JCR Item": [{
            "fieldname": "excess_days",
            "label": "Excess Days",
            "fieldtype": "Float",
            "insert_after": "contract_days",
            "in_list_view": 1,
            "columns": 1,
        }]
    })
    frappe.clear_cache(doctype="JCR")
