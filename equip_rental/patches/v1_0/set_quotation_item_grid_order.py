import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DT = "Quotation Item"

# Desired left-to-right order of the Items grid on Quotation
DESIRED = [
    "item_code", "is_job_type_item", "item_name", "description",
    "custom_length", "custom_breadth", "custom_height", "qty",
    "rotation_qty", "period", "rate", "amount",
    "contract_days", "excess_charge", "excess_period",
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
    create_custom_fields({DT: [{
        "fieldname": "is_job_type_item",
        "label": "Is Job Type",
        "fieldtype": "Check",
        "fetch_from": "item_code.is_job_type_item",
        "read_only": 1,
        "insert_after": "item_code",
        "in_list_view": 1,
        "columns": 1,
    }]})
    frappe.clear_cache(doctype=DT)

    # Grid columns: show exactly these, width 1 each. Property Setters are
    # used (not Custom Field edits) so fixtures can't clobber them on migrate.
    for fn in DESIRED:
        _ps(fn, "in_list_view", "1", "Check")
        _ps(fn, "columns", "1", "Int")
    _ps("uom", "in_list_view", "0", "Check")

    # Permute the desired fields among the slots they already occupy,
    # keeping section/column breaks where they are.
    current = [df.fieldname for df in frappe.get_meta(DT, cached=False).fields]
    present = [fn for fn in DESIRED if fn in current]
    slots = sorted(current.index(fn) for fn in present)
    new_order = list(current)
    for slot, fn in zip(slots, present):
        new_order[slot] = fn

    frappe.make_property_setter({
        "doctype": DT,
        "doctype_or_field": "DocType",
        "property": "field_order",
        "value": json.dumps(new_order),
        "property_type": "Data",
    }, ignore_validate=True)
    frappe.clear_cache(doctype=DT)
