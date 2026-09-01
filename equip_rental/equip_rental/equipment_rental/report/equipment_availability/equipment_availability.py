import frappe
from frappe import _

from equip_rental.utils.availability import get_conflicts


def execute(filters=None):
    filters = frappe._dict(filters or {})

    equipment_filters = {"status": ["not in", ["Retired"]]}
    if filters.equipment_category:
        equipment_filters["equipment_category"] = filters.equipment_category
    if filters.equipment:
        equipment_filters["name"] = filters.equipment

    rows = []
    for unit in frappe.get_all("Rental Equipment", filters=equipment_filters,
                               fields=["name", "equipment_name", "equipment_category",
                                       "status", "current_location"],
                               order_by="equipment_name asc"):
        conflicts = get_conflicts(unit.name, filters.from_date, filters.to_date)
        if conflicts:
            for conflict in conflicts:
                rows.append({
                    "equipment": unit.name, "equipment_name": unit.equipment_name,
                    "equipment_category": unit.equipment_category,
                    "status": unit.status, "available": 0,
                    "blocked_by": "{0}: {1}".format(conflict["doctype"],
                                                    conflict["name"]),
                    "blocked_from": conflict["from_date"],
                    "blocked_to": conflict["to_date"],
                    "location": unit.current_location,
                })
        else:
            rows.append({
                "equipment": unit.name, "equipment_name": unit.equipment_name,
                "equipment_category": unit.equipment_category,
                "status": unit.status, "available": 1,
                "location": unit.current_location,
            })

    columns = [
        {"fieldname": "equipment", "label": _("Equipment"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 130},
        {"fieldname": "equipment_name", "label": _("Name"), "fieldtype": "Data",
         "width": 180},
        {"fieldname": "equipment_category", "label": _("Category"), "fieldtype": "Link",
         "options": "Equipment Category", "width": 140},
        {"fieldname": "status", "label": _("Current Status"), "fieldtype": "Data",
         "width": 120},
        {"fieldname": "available", "label": _("Free in Period"), "fieldtype": "Check",
         "width": 110},
        {"fieldname": "blocked_by", "label": _("Blocked By"), "fieldtype": "Data",
         "width": 220},
        {"fieldname": "blocked_from", "label": _("From"), "fieldtype": "Date",
         "width": 100},
        {"fieldname": "blocked_to", "label": _("To"), "fieldtype": "Date", "width": 100},
        {"fieldname": "location", "label": _("Location"), "fieldtype": "Link",
         "options": "Warehouse", "width": 130},
    ]
    return columns, rows
