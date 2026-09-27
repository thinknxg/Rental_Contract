import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    existing = {f.fieldname for f in frappe.get_meta("JCR Item").fields}
    if "qty" not in existing:
        create_custom_fields({"JCR Item": [{
            "fieldname": "qty",
            "label": "Qty",
            "fieldtype": "Float",
            "insert_after": "job_description",
            "in_list_view": 1,
            "columns": 1,
        }]}, update=False)
    frappe.clear_cache(doctype="JCR")
