import frappe


def execute():
    frappe.make_property_setter({
        "doctype": "Sales Order Item",
        "fieldname": "item_code",
        "property": "label",
        "value": "Item Code",
        "property_type": "Data",
    })
    frappe.make_property_setter({
        "doctype": "Sales Order Item",
        "fieldname": "item_code",
        "property": "reqd",
        "value": "1",
        "property_type": "Check",
    })
    frappe.clear_cache(doctype="Sales Order")
