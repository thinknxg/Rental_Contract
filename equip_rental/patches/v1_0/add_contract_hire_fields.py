import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    custom_fields = {
        "Quotation Item": [
            dict(fieldname="custom_rate_type", label="Rate Type", fieldtype="Select",
                 options="\nM3\nSQM\nNos\nDay\nMonth\nLumpsum",
                 insert_after="description"),
            dict(fieldname="custom_length", label="Length", fieldtype="Float",
                 insert_after="custom_rate_type"),
            dict(fieldname="custom_breadth", label="Breadth", fieldtype="Float",
                 insert_after="custom_length"),
            dict(fieldname="custom_height", label="Height", fieldtype="Float",
                 insert_after="custom_breadth"),
            dict(fieldname="custom_no_of_locations", label="No. of Locations", fieldtype="Float",
                 insert_after="custom_height"),
            dict(fieldname="custom_calculated_volume", label="Calculated Volume", fieldtype="Float",
                 read_only=1, insert_after="custom_no_of_locations"),
            dict(fieldname="custom_duration", label="Duration", fieldtype="Float",
                 insert_after="custom_calculated_volume"),
            dict(fieldname="custom_period", label="Period", fieldtype="Select",
                 options="\nDay\nWeek\nMonth\nYear",
                 insert_after="custom_duration"),
            dict(fieldname="custom_start_date", label="Start Date", fieldtype="Date",
                 insert_after="custom_period"),
            dict(fieldname="custom_end_date", label="End Date", fieldtype="Date",
                 insert_after="custom_start_date"),
            dict(fieldname="custom_site", label="Site", fieldtype="Link", options="Project Site",
                 insert_after="custom_end_date"),
            dict(fieldname="custom_remarks", label="Remarks", fieldtype="Small Text",
                 insert_after="custom_site"),
        ]
    }
    create_custom_fields(custom_fields, update=True)
