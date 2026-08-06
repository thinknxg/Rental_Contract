import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    period_days = date_diff(filters.to_date, filters.from_date) + 1
    if period_days <= 0:
        frappe.throw(_("To Date must be on or after From Date"))

    equipment_filters = {}
    if filters.equipment_category:
        equipment_filters["equipment_category"] = filters.equipment_category
    if filters.equipment:
        equipment_filters["name"] = filters.equipment

    equipment = frappe.get_all("Rental Equipment", filters=equipment_filters,
                               fields=["name", "equipment_name", "equipment_category",
                                       "status", "ownership"])

    rows = []
    for unit in equipment:
        rented = _days_on_hire(unit.name, filters.from_date, filters.to_date,
                               "Customer Rental")
        internal = _days_on_hire(unit.name, filters.from_date, filters.to_date,
                                 "Internal Use")
        down = _days_down(unit.name, filters.from_date, filters.to_date)
        revenue = _revenue(unit.name, filters.from_date, filters.to_date)
        used = rented + internal
        rows.append({
            "equipment": unit.name,
            "equipment_name": unit.equipment_name,
            "equipment_category": unit.equipment_category,
            "ownership": unit.ownership,
            "rented_days": rented,
            "internal_days": internal,
            "downtime_days": down,
            "idle_days": max(period_days - used - down, 0),
            "utilization": flt(used * 100.0 / period_days, 1),
            "revenue": revenue,
        })

    columns = [
        {"fieldname": "equipment", "label": _("Equipment"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 130},
        {"fieldname": "equipment_name", "label": _("Name"), "fieldtype": "Data",
         "width": 180},
        {"fieldname": "equipment_category", "label": _("Category"), "fieldtype": "Link",
         "options": "Equipment Category", "width": 140},
        {"fieldname": "ownership", "label": _("Ownership"), "fieldtype": "Data",
         "width": 100},
        {"fieldname": "rented_days", "label": _("Rented Days"), "fieldtype": "Float",
         "width": 110},
        {"fieldname": "internal_days", "label": _("Internal Days"), "fieldtype": "Float",
         "width": 110},
        {"fieldname": "downtime_days", "label": _("Downtime Days"), "fieldtype": "Float",
         "width": 120},
        {"fieldname": "idle_days", "label": _("Idle Days"), "fieldtype": "Float",
         "width": 100},
        {"fieldname": "utilization", "label": _("Utilization %"), "fieldtype": "Percent",
         "width": 120},
        {"fieldname": "revenue", "label": _("Revenue"), "fieldtype": "Currency",
         "width": 130},
    ]

    chart = {
        "data": {
            "labels": [r["equipment_name"] for r in rows][:15],
            "datasets": [{"name": _("Utilization %"),
                          "values": [r["utilization"] for r in rows][:15]}],
        },
        "type": "bar",
    }
    return columns, rows, None, chart


def _days_on_hire(equipment, from_date, to_date, contract_type):
    rows = frappe.db.sql("""
        select i.charge_from,
            coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                     c.expected_end_date) as end_date
        from `tabRental Contract Item` i
        inner join `tabRental Contract` c on c.name = i.parent
        where i.equipment = %(equipment)s and c.docstatus = 1
            and c.contract_type = %(contract_type)s
            and c.status != 'Cancelled'
            and i.charge_from <= %(to_date)s
            and (coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                          c.expected_end_date) is null
                 or coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                             c.expected_end_date) >= %(from_date)s)
    """, {"equipment": equipment, "contract_type": contract_type,
          "from_date": from_date, "to_date": to_date}, as_dict=True)

    return _overlap_days(rows, "charge_from", "end_date", from_date, to_date)


def _days_down(equipment, from_date, to_date):
    rows = frappe.db.sql("""
        select date(from_datetime) as start_date, date(to_datetime) as end_date
        from `tabRental Maintenance Log`
        where equipment = %(equipment)s and status != 'Cancelled'
            and date(from_datetime) <= %(to_date)s
            and (to_datetime is null or date(to_datetime) >= %(from_date)s)
    """, {"equipment": equipment, "from_date": from_date, "to_date": to_date},
        as_dict=True)
    return _overlap_days(rows, "start_date", "end_date", from_date, to_date)


def _overlap_days(rows, start_key, end_key, from_date, to_date):
    total = 0
    window_start, window_end = getdate(from_date), getdate(to_date)
    for row in rows:
        start = max(getdate(row.get(start_key)), window_start)
        end = getdate(row.get(end_key)) if row.get(end_key) else window_end
        end = min(end, window_end)
        if end >= start:
            total += date_diff(end, start) + 1
    return total


def _revenue(equipment, from_date, to_date):
    value = frappe.db.sql("""
        select sum(sii.base_net_amount)
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        where si.docstatus = 1 and sii.rental_equipment = %(equipment)s
            and si.posting_date between %(from_date)s and %(to_date)s
    """, {"equipment": equipment, "from_date": from_date, "to_date": to_date})
    return flt(value[0][0]) if value and value[0][0] else 0.0
