import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = []
    for fn in ("custom_length", "custom_breadth", "custom_height"):
        if frappe.db.exists("Custom Field", f"Sales Order Item-{fn}"):
            continue
        src = frappe.db.get_value(
            "Custom Field", f"Quotation Item-{fn}",
            ["label", "fieldtype", "precision", "default"], as_dict=True,
        )
        if not src:
            continue
        fields.append({
            "fieldname": fn,
            "label": src.label,
            "fieldtype": src.fieldtype,
            "precision": src.precision,
            "default": src.default,
            "insert_after": "uom",
            "in_list_view": 1,
            "columns": 1,
        })
    if fields:
        create_custom_fields({"Sales Order Item": fields}, update=False)
    frappe.clear_cache(doctype="Sales Order")
