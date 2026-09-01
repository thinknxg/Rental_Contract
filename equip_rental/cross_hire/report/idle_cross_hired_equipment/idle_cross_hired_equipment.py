import frappe
from frappe import _

from equip_rental.utils.cross_hire import get_idle_cross_hired_units


def execute(filters=None):
    filters = frappe._dict(filters or {})
    rows = get_idle_cross_hired_units(filters.min_days)
    if filters.supplier:
        rows = [r for r in rows if r.get("supplier") == filters.supplier]

    columns = [
        {"fieldname": "equipment", "label": _("Equipment"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 130},
        {"fieldname": "equipment_name", "label": _("Name"), "fieldtype": "Data",
         "width": 200},
        {"fieldname": "supplier", "label": _("Vendor"), "fieldtype": "Link",
         "options": "Supplier", "width": 160},
        {"fieldname": "cross_hire_order", "label": _("Order"), "fieldtype": "Link",
         "options": "Cross Hire Order", "width": 130},
        {"fieldname": "on_hire_date", "label": _("On Hire Since"), "fieldtype": "Date",
         "width": 110},
        {"fieldname": "idle_since", "label": _("Idle Since"), "fieldtype": "Date",
         "width": 110},
        {"fieldname": "idle_days", "label": _("Idle Days"), "fieldtype": "Int",
         "width": 100},
        {"fieldname": "rate", "label": _("Vendor Rate"), "fieldtype": "Currency",
         "width": 110},
        {"fieldname": "rate_basis", "label": _("Basis"), "fieldtype": "Data",
         "width": 80},
        {"fieldname": "idle_cost", "label": _("Idle Cost"), "fieldtype": "Currency",
         "width": 120},
    ]

    chart = {
        "data": {"labels": [r["equipment_name"] for r in rows][:12],
                 "datasets": [{"name": _("Idle Cost"),
                               "values": [r["idle_cost"] for r in rows][:12]}]},
        "type": "bar",
    }
    summary = [{"label": _("Units Idle"), "value": len(rows), "indicator": "Orange"},
               {"label": _("Cash Burning"),
                "value": sum(r["idle_cost"] for r in rows), "datatype": "Currency",
                "indicator": "Red"}]
    return columns, rows, None, chart, summary
