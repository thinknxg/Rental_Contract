import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def set_insert_after(doctype, fieldname, insert_after):
    filters = {"doc_type": doctype, "field_name": fieldname, "property": "insert_after"}
    if frappe.db.exists("Property Setter", filters):
        frappe.db.set_value("Property Setter", filters, "value", insert_after)
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": doctype,
            "field_name": fieldname,
            "property": "insert_after",
            "property_type": "Data",
            "value": insert_after,
            "doctype_or_field": "DocField",
        }).insert()


def execute():
    # Custom fields: reorder via create_custom_fields
    custom_fields = {
        "Quotation Item": [
            dict(fieldname="custom_length", insert_after="uom"),
            dict(fieldname="custom_breadth", insert_after="custom_length"),
            dict(fieldname="custom_height", insert_after="custom_breadth"),
            dict(fieldname="custom_duration", insert_after="qty"),
            dict(fieldname="period", insert_after="custom_duration"),
        ]
    }
    create_custom_fields(custom_fields, update=True)

    # Core/standard fields: reorder via Property Setter
    set_insert_after("Quotation Item", "uom", "item_code")
    set_insert_after("Quotation Item", "qty", "custom_height")
    set_insert_after("Quotation Item", "rate", "period")
    set_insert_after("Quotation Item", "amount", "rate")

    # Rename Rate's label to "Unit Price"
    label_filters = {"doc_type": "Quotation Item", "field_name": "rate", "property": "label"}
    if frappe.db.exists("Property Setter", label_filters):
        frappe.db.set_value("Property Setter", label_filters, "value", "Unit Price")
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": "Quotation Item",
            "field_name": "rate",
            "property": "label",
            "property_type": "Data",
            "value": "Unit Price",
            "doctype_or_field": "DocField",
        }).insert()

    frappe.clear_cache(doctype="Quotation Item")
    frappe.db.commit()
