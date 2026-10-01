import json

import frappe

DT = "Sales Order Item"

# Same left-to-right order as the final Quotation Items grid
DESIRED = [
    "item_code", "item_name", "description", "uom",
    "custom_length", "custom_breadth", "custom_height", "qty",
    "contract_days", "period", "rate", "amount",
    "custom_contract_days", "excess_charge", "excess_period",
]


def _ps(fieldname, prop, value, ptype):
    frappe.make_property_setter({
        "doctype": DT,
        "fieldname": fieldname,
        "property": prop,
        "value": value,
        "property_type": ptype,
    })


def execute():
    for fn in DESIRED:
        _ps(fn, "in_list_view", "1", "Check")
        _ps(fn, "columns", "1", "Int")
    frappe.clear_cache(doctype=DT)

    ps_name = f"{DT}-main-field_order"
    if frappe.db.exists("Property Setter", ps_name):
        current = json.loads(frappe.db.get_value("Property Setter", ps_name, "value"))
    else:
        current = [df.fieldname for df in frappe.get_meta(DT, cached=False).fields]

    present = [fn for fn in DESIRED if fn in current]
    slots = sorted(current.index(fn) for fn in present)
    new_order = list(current)
    for slot, fn in zip(slots, present):
        new_order[slot] = fn

    if frappe.db.exists("Property Setter", ps_name):
        frappe.db.set_value("Property Setter", ps_name, "value", json.dumps(new_order))
    else:
        frappe.make_property_setter({
            "doctype": DT,
            "doctype_or_field": "DocType",
            "property": "field_order",
            "value": json.dumps(new_order),
            "property_type": "Data",
        }, ignore_validate=True)
    frappe.clear_cache(doctype=DT)
