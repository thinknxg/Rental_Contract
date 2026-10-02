import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
    "Purchase Order": [
        {"fieldname": "cross_hire_order", "label": "Cross Hire Order",
         "fieldtype": "Link", "options": "Cross Hire Order", "insert_after": "project",
         "read_only": 1, "no_copy": 1},
    ],
    "Purchase Receipt": [
        {"fieldname": "cross_hire_order", "label": "Cross Hire Order",
         "fieldtype": "Link", "options": "Cross Hire Order", "insert_after": "project",
         "read_only": 1, "no_copy": 1},
        {"fieldname": "cross_hire_receipt", "label": "Cross Hire Receipt",
         "fieldtype": "Link", "options": "Cross Hire Receipt",
         "insert_after": "cross_hire_order", "read_only": 1, "no_copy": 1,
         "depends_on": "eval:!doc.is_return"},
        {"fieldname": "cross_hire_off_hire_note", "label": "Cross Hire Off Hire Note",
         "fieldtype": "Link", "options": "Cross Hire Off Hire Note",
         "insert_after": "cross_hire_receipt", "read_only": 1, "no_copy": 1,
         "depends_on": "is_return"},
    ],
    "Purchase Invoice": [
        {"fieldname": "cross_hire_order", "label": "Cross Hire Order",
         "fieldtype": "Link", "options": "Cross Hire Order", "insert_after": "project",
         "read_only": 1, "no_copy": 1},
        {"fieldname": "cross_hire_reconciliation", "label": "Cross Hire Reconciliation",
         "fieldtype": "Link", "options": "Cross Hire Invoice Reconciliation",
         "insert_after": "cross_hire_order", "read_only": 1, "no_copy": 1},
    ],
    "Item": [
        {"fieldname": "is_cross_hire_item", "label": "Is Cross Hire Item",
         "fieldtype": "Check", "insert_after": "is_rental_item",
         "description": "Stock item representing equipment hired in from a vendor. "
                        "Always received at zero valuation."},
    ],
}


def execute():
    create_custom_fields(CUSTOM_FIELDS)
    for dt in CUSTOM_FIELDS:
        frappe.clear_cache(doctype=dt)
