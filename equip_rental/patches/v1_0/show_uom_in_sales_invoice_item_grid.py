import frappe


def execute():
    frappe.make_property_setter({
        "doctype": "Sales Invoice Item",
        "fieldname": "uom",
        "property": "in_list_view",
        "value": "1",
        "property_type": "Check",
    })
    frappe.make_property_setter({
        "doctype": "Sales Invoice Item",
        "fieldname": "uom",
        "property": "columns",
        "value": "1",
        "property_type": "Int",
    })
    frappe.clear_cache(doctype="Sales Invoice Item")
