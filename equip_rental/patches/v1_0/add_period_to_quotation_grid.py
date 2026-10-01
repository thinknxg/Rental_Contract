import json

import frappe

DT = "Quotation Item"


def execute():
    for prop, value, ptype in (("in_list_view", "1", "Check"), ("columns", "1", "Int")):
        frappe.make_property_setter({
            "doctype": DT,
            "fieldname": "period",
            "property": prop,
            "value": value,
            "property_type": ptype,
        })

    # Period directly after Duration (rotation_qty)
    ps_name = f"{DT}-main-field_order"
    if frappe.db.exists("Property Setter", ps_name):
        order = json.loads(frappe.db.get_value("Property Setter", ps_name, "value"))
        if "period" in order and "rotation_qty" in order:
            order.remove("period")
            order.insert(order.index("rotation_qty") + 1, "period")
            frappe.db.set_value("Property Setter", ps_name, "value", json.dumps(order))
    frappe.clear_cache(doctype=DT)
