import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Quotation Item": [
            dict(fieldname="custom_rate_type", label="Rate Type", in_list_view=0),
            dict(fieldname="custom_no_of_locations", label="No. of Locations", in_list_view=0),
            dict(fieldname="custom_site", label="Site", in_list_view=0),
            dict(fieldname="custom_period", label="Period", in_list_view=0),
            dict(fieldname="custom_calculated_volume", label="Calculated Volume", in_list_view=0),
        ]
    }
    create_custom_fields(custom_fields, update=True)

    frappe.db.set_value(
        "Property Setter",
        {"doc_type": "Quotation Item", "field_name": "uom", "property": "in_list_view"},
        "value", "1",
    )
    if not frappe.db.exists(
        "Property Setter",
        {"doc_type": "Quotation Item", "field_name": "uom", "property": "in_list_view"},
    ):
        ps = frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": "Quotation Item",
            "field_name": "uom",
            "property": "in_list_view",
            "property_type": "Check",
            "value": "1",
            "doctype_or_field": "DocField",
        })
        ps.insert()
    frappe.clear_cache(doctype="Quotation Item")
