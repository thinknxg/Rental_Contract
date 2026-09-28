import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

DT = "Sales Order Item"

# Same left-to-right order as the Quotation Items grid
DESIRED = [
    "item_code", "is_job_type_item", "item_name", "description",
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
    # Reuse Quotation Item's Period definition so both doctypes match
    q_period = frappe.get_meta("Quotation Item", cached=False).get_field("period")
    period_options = (q_period.options if q_period else None) or "Day\nWeek\nMonth\nYear"

    create_custom_fields({DT: [
        {
            "fieldname": "is_job_type_item",
            "label": "Is Job Type",
            "fieldtype": "Check",
            "fetch_from": "item_code.is_job_type_item",
            "read_only": 1,
            "insert_after": "item_code",
            "in_list_view": 1,
            "columns": 1,
        },
        {
            "fieldname": "period",
            "label": "Period",
            "fieldtype": "Select",
            "options": period_options,
            "insert_after": "contract_days",
            "in_list_view": 1,
            "columns": 1,
        },
    ]})
    frappe.clear_cache(doctype=DT)

    # Labels via Property Setter so fixtures can't revert them on migrate
    _ps("contract_days", "label", "Duration", "Data")
    _ps("rate", "label", "Unit Price", "Data")

    for fn in DESIRED:
        _ps(fn, "in_list_view", "1", "Check")
        _ps(fn, "columns", "1", "Int")
    _ps("delivery_date", "in_list_view", "0", "Check")

    # Permute the desired fields among the slots they already occupy,
    # keeping section/column breaks where they are.
    current = [df.fieldname for df in frappe.get_meta(DT, cached=False).fields]
    present = [fn for fn in DESIRED if fn in current]
    slots = sorted(current.index(fn) for fn in present)
    new_order = list(current)
    for slot, fn in zip(slots, present):
        new_order[slot] = fn

    # make_property_setter can't find an existing field_order setter (its
    # field_name is NULL), so update the existing record directly.
    ps_name = f"{DT}-main-field_order"
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
