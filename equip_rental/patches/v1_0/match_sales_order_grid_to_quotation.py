import json

import frappe

DT = "Sales Order Item"


def execute():
    # Item Code and UOM both visible, width 1, same as the Quotation grid
    for fn in ("item_code", "uom"):
        for prop, value, ptype in (("in_list_view", "1", "Check"), ("columns", "1", "Int")):
            frappe.make_property_setter({
                "doctype": DT,
                "fieldname": fn,
                "property": prop,
                "value": value,
                "property_type": ptype,
            })

    # UOM directly after Item Code in the field order
    ps_name = f"{DT}-main-field_order"
    if frappe.db.exists("Property Setter", ps_name):
        order = json.loads(frappe.db.get_value("Property Setter", ps_name, "value"))
        if "uom" in order and "item_code" in order:
            order.remove("uom")
            order.insert(order.index("item_code") + 1, "uom")
            frappe.db.set_value("Property Setter", ps_name, "value", json.dumps(order))
    frappe.clear_cache(doctype=DT)
