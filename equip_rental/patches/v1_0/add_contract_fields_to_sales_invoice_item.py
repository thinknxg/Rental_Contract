import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Sales Invoice Item": [
            {"fieldname": "contract_from_date", "label": "Contract From", "fieldtype": "Date",
             "insert_after": "qty", "in_list_view": 1, "columns": 1},
            {"fieldname": "contract_to_date", "label": "Contract To", "fieldtype": "Date",
             "insert_after": "contract_from_date", "in_list_view": 1, "columns": 1},
            {"fieldname": "contract_days", "label": "Contract Days", "fieldtype": "Float",
             "insert_after": "contract_to_date", "in_list_view": 1, "columns": 1},
            {"fieldname": "contract_amount", "label": "Contract Amount", "fieldtype": "Currency",
             "insert_after": "contract_days", "in_list_view": 1, "columns": 1},
            # re-anchor the excess block after the contract block
            {"fieldname": "excess_charge", "label": "Excess Charge", "fieldtype": "Currency",
             "insert_after": "contract_amount", "in_list_view": 1, "columns": 1},
        ]
    })
    frappe.clear_cache(doctype="Sales Invoice Item")
