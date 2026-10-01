import json

import frappe

DT = "Quotation Item"


def execute():
    for fn in ("item_name", "description"):
        for prop, value, ptype in (("in_list_view", "1", "Check"), ("columns", "1", "Int")):
            frappe.make_property_setter({
                "doctype": DT,
                "fieldname": fn,
                "property": prop,
                "value": value,
                "property_type": ptype,
            })

    # Item Name, Description directly after Item Code
    ps_name = f"{DT}-main-field_order"
    if frappe.db.exists("Property Setter", ps_name):
        order = json.loads(frappe.db.get_value("Property Setter", ps_name, "value"))
        if "item_code" in order:
            for fn in ("description", "item_name"):
                if fn in order:
                    order.remove(fn)
                    order.insert(order.index("item_code") + 1, fn)
            frappe.db.set_value("Property Setter", ps_name, "value", json.dumps(order))
    frappe.clear_cache(doctype=DT)
