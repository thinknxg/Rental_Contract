import frappe
from frappe import _
from frappe.utils import getdate, nowdate

BLOCKING_ITEM_STATUS = ("Pending Dispatch", "On Rent")
UNAVAILABLE_STATUS = ("Out of Service", "Retired")


def get_conflicts(equipment, from_date, to_date, ignore_contract=None,
                  ignore_reservation=None):
    """Return a list of blocking documents for a period."""
    from_date, to_date = getdate(from_date), getdate(to_date)
    conflicts = []

    contract_filter = ""
    values = {"equipment": equipment, "from_date": from_date, "to_date": to_date}
    if ignore_contract:
        contract_filter = " and c.name != %(ignore)s"
        values["ignore"] = ignore_contract

    rows = frappe.db.sql("""
        select c.name, c.start_date,
            coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                     c.expected_end_date) as end_date
        from `tabRental Contract Item` i
        inner join `tabRental Contract` c on c.name = i.parent
        where i.equipment = %(equipment)s
            and c.docstatus = 1
            and c.status not in ('Closed', 'Cancelled')
            and i.item_status in ('Pending Dispatch', 'On Rent')
            and i.charge_from <= %(to_date)s
            and (coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                          c.expected_end_date) is null
                 or coalesce(i.off_rent_date, i.charge_upto, c.actual_end_date,
                             c.expected_end_date) >= %(from_date)s)
            {contract_filter}
    """.format(contract_filter=contract_filter), values, as_dict=True)
    for row in rows:
        conflicts.append({"doctype": "Rental Contract", "name": row.name,
                          "from_date": row.start_date, "to_date": row.end_date})

    res_values = {"equipment": equipment, "from_date": from_date, "to_date": to_date}
    res_filter = ""
    if ignore_reservation:
        res_filter = " and r.name != %(ignore_res)s"
        res_values["ignore_res"] = ignore_reservation

    rows = frappe.db.sql("""
        select r.name, r.from_date, r.to_date
        from `tabRental Reservation Item` ri
        inner join `tabRental Reservation` r on r.name = ri.parent
        where ri.equipment = %(equipment)s
            and r.status = 'Confirmed'
            and r.from_date <= %(to_date)s and r.to_date >= %(from_date)s
            {res_filter}
    """.format(res_filter=res_filter), res_values, as_dict=True)
    for row in rows:
        conflicts.append({"doctype": "Rental Reservation", "name": row.name,
                          "from_date": row.from_date, "to_date": row.to_date})

    rows = frappe.db.sql("""
        select name, from_datetime, to_datetime
        from `tabRental Maintenance Log`
        where equipment = %(equipment)s
            and status in ('Open', 'In Progress')
            and date(from_datetime) <= %(to_date)s
            and (to_datetime is null or date(to_datetime) >= %(from_date)s)
    """, {"equipment": equipment, "from_date": from_date, "to_date": to_date}, as_dict=True)
    for row in rows:
        conflicts.append({"doctype": "Rental Maintenance Log", "name": row.name,
                          "from_date": row.from_datetime, "to_date": row.to_datetime})

    return conflicts


def is_available(equipment, from_date, to_date, ignore_contract=None,
                 ignore_reservation=None):
    status = frappe.db.get_value("Rental Equipment", equipment, "status")
    if status in UNAVAILABLE_STATUS:
        return False
    return not get_conflicts(equipment, from_date, to_date, ignore_contract,
                             ignore_reservation)


def validate_availability(equipment, from_date, to_date, ignore_contract=None):
    conflicts = get_conflicts(equipment, from_date, to_date, ignore_contract)
    if conflicts:
        first = conflicts[0]
        frappe.throw(
            _("{0} is not available between {1} and {2}. Blocked by {3} {4}.").format(
                frappe.bold(equipment), from_date, to_date,
                first["doctype"], first["name"]),
            title=_("Equipment Not Available"))


@frappe.whitelist()
def get_available_equipment(from_date=None, to_date=None, equipment_category=None,
                            company=None, published_only=0, limit=100):
    from_date = getdate(from_date or nowdate())
    to_date = getdate(to_date or from_date)

    filters = {"status": ["not in", UNAVAILABLE_STATUS]}
    if equipment_category:
        filters["equipment_category"] = equipment_category
    if company:
        filters["company"] = company
    if int(published_only or 0):
        filters["published"] = 1

    rows = frappe.get_all(
        "Rental Equipment", filters=filters,
        fields=["name", "equipment_name", "equipment_category", "model", "status",
                "image", "route", "daily_rate", "weekly_rate", "monthly_rate",
                "hourly_rate", "short_description"],
        order_by="equipment_name asc", limit_page_length=int(limit))

    available = []
    for row in rows:
        if is_available(row.name, from_date, to_date):
            available.append(row)
    return available


@frappe.whitelist()
def get_equipment_calendar(equipment, from_date, to_date):
    """Booked blocks for a single unit - used by the availability calendar."""
    return get_conflicts(equipment, from_date, to_date)
