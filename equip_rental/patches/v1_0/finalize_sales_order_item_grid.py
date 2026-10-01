import frappe

DT = "Sales Order Item"


def execute():
    frappe.make_property_setter({
        "doctype": DT, "fieldname": "item_code",
        "property": "in_list_view", "value": "1", "property_type": "Check",
    })
    frappe.make_property_setter({
        "doctype": DT, "fieldname": "item_code",
        "property": "columns", "value": "1", "property_type": "Int",
    })
    frappe.make_property_setter({
        "doctype": DT, "fieldname": "job_no",
        "property": "in_list_view", "value": "0", "property_type": "Check",
    })
    frappe.clear_cache(doctype=DT)
