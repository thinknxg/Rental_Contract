import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Quotation Item": [
            dict(fieldname="custom_duration", label="Duration",
                 insert_after="custom_calculated_volume", in_list_view=0),
        ]
    }
    create_custom_fields(custom_fields, update=True)
