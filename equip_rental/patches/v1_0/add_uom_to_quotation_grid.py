import json

import frappe

DT = "Quotation Item"


def execute():
    for prop, value, ptype in (("in_list_view", "1", "Check"), ("columns", "1", "Int")):
        frappe.make_property_setter({
            "doctype": DT,
            "fieldname": "uom",
            "property": prop,
            "value": value,
            "property_type": ptype,
        })

    # Place UOM directly after Qty in the field order
    ps_name = f"{DT}-main-field_order"
    if frappe.db.exists("Property Setter", ps_name):
        order = json.loads(frappe.db.get_value("Property Setter", ps_name, "value"))
        if "uom" in order and "qty" in order:
            order.remove("uom")
            order.insert(order.index("qty") + 1, "uom")
            frappe.db.set_value("Property Setter", ps_name, "value", json.dumps(order))
    frappe.clear_cache(doctype=DT)
