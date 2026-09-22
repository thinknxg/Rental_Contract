import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Quotation Item": [
            dict(fieldname="custom_rate_type", label="Rate Type", fieldtype="Select",
                 options="\nM3\nSQM\nNos\nDay\nMonth\nLumpsum",
                 insert_after="description", in_list_view=1, columns=2),
            dict(fieldname="custom_length", label="Length", fieldtype="Float",
                 insert_after="custom_rate_type", in_list_view=1, columns=1),
            dict(fieldname="custom_breadth", label="Breadth", fieldtype="Float",
                 insert_after="custom_length", in_list_view=1, columns=1),
            dict(fieldname="custom_height", label="Height", fieldtype="Float",
                 insert_after="custom_breadth", in_list_view=1, columns=1),
            dict(fieldname="custom_no_of_locations", label="No. of Locations", fieldtype="Float",
                 insert_after="custom_height", in_list_view=1, columns=1),
            dict(fieldname="custom_calculated_volume", label="Calculated Volume", fieldtype="Float",
                 read_only=1, insert_after="custom_no_of_locations", in_list_view=1, columns=2),
            dict(fieldname="custom_duration", label="Duration", fieldtype="Float",
                 insert_after="custom_calculated_volume", in_list_view=1, columns=1),
            dict(fieldname="custom_period", label="Period", fieldtype="Select",
                 options="\nDay\nWeek\nMonth\nYear",
                 insert_after="custom_duration", in_list_view=1, columns=1),
            dict(fieldname="custom_site", label="Site", fieldtype="Link", options="Project Site",
                 insert_after="custom_end_date", in_list_view=1, columns=2),
        ]
    }
    create_custom_fields(custom_fields, update=True)
