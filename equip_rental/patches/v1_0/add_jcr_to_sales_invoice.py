import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    if not frappe.get_meta("Sales Invoice").has_field("jcr"):
        create_custom_fields({"Sales Invoice": [{
            "fieldname": "jcr",
            "label": "JCR",
            "fieldtype": "Link",
            "options": "JCR",
            "insert_after": "customer",
            "read_only": 1,
            "no_copy": 1,
            "print_hide": 1,
        }]}, update=False)
    frappe.clear_cache(doctype="Sales Invoice")
