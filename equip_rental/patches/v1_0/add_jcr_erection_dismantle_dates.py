import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "JCR Item": [
            dict(fieldname="custom_erection_date", label="Erection Date", fieldtype="Date",
                 insert_after="job_description", in_list_view=1),
            dict(fieldname="custom_dismantle_date", label="Dismantle Date", fieldtype="Date",
                 insert_after="custom_erection_date", in_list_view=1),
        ]
    }
    create_custom_fields(custom_fields, update=True)
