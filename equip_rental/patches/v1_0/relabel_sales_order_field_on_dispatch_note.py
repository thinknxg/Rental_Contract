import frappe


def execute():
    frappe.make_property_setter({
        "doctype": "Rental Dispatch Note",
        "fieldname": "sales_order",
        "property": "label",
        "value": "Rental Contract",
        "property_type": "Data",
    })
    frappe.clear_cache(doctype="Rental Dispatch Note")
