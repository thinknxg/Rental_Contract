import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields({
        "Sales Invoice Item": [
            {
                "fieldname": "custom_excess_charge",
                "label": "Excess Charge",
                "fieldtype": "Currency",
                "insert_after": "qty",
                "in_list_view": 1,
                "columns": 1,
            },
            {
                "fieldname": "custom_excess_days",
                "label": "Excess Days",
                "fieldtype": "Float",
                "insert_after": "custom_excess_charge",
                "in_list_view": 1,
                "columns": 1,
            },
        ]
    })

    # Base Amount was added by an earlier patch; hide it from the grid
    # since only Excess Charge, Excess Days, Excess Amount are wanted.
    if frappe.db.exists("Custom Field", "Sales Invoice Item-custom_base_amount"):
        frappe.make_property_setter({
            "doctype": "Sales Invoice Item",
            "fieldname": "custom_base_amount",
            "property": "in_list_view",
            "value": "0",
            "property_type": "Check",
        })

    frappe.clear_cache(doctype="Sales Invoice")
