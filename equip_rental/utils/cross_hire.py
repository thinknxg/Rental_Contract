"""Cross hire: equipment hired in from a vendor, then used internally or
re-hired to a customer, and returned to the vendor at the end of the hire.

The cost side lives here. Once a unit is received it becomes an ordinary
Rental Equipment record, so contracts, dispatch, availability and customer
invoicing all work unchanged - with one extra constraint: a cross-hired unit
can never be committed beyond the window we hold it from the vendor.
"""

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

from equip_rental.utils.common import get_settings
from equip_rental.utils.pricing import get_billable_units


# ------------------------------------------------------------------ hire window
def get_hire_window(equipment):
    row = frappe.db.get_value(
        "Rental Equipment", equipment,
        ["ownership", "hire_available_from", "hire_available_upto", "cross_hire_order"],
        as_dict=True)
    if not row or row.ownership != "Cross-Hired":
        return None
    return row


def validate_hire_window(equipment, from_date, to_date):
    """A cross-hired unit cannot be promised to a customer for longer than we
    hold it. Extend the Cross Hire Order first."""
    window = get_hire_window(equipment)
    if not window:
        return

    from_date, to_date = getdate(from_date), getdate(to_date or from_date)

    if window.hire_available_from and from_date < getdate(window.hire_available_from):
        frappe.throw(
            _("{0} is cross-hired from {1} and is only on hire to us from {2}.").format(
                frappe.bold(equipment), window.cross_hire_order,
                window.hire_available_from), title=_("Outside Cross Hire Window"))

    if window.hire_available_upto and to_date > getdate(window.hire_available_upto):
        frappe.throw(
            _("{0} is cross-hired under {1} and must go back to the vendor on {2}. "
              "Extend the Cross Hire Order before committing to {3}.").format(
                frappe.bold(equipment), window.cross_hire_order,
                window.hire_available_upto, to_date),
            title=_("Outside Cross Hire Window"))


# ------------------------------------------------------------------ costing
def item_charge_period(item, order, upto=None):
    """Vendor-chargeable window for one cross hire order line."""
    start = getdate(item.on_hire_date or item.expected_from_date or order.from_date)
    end_candidates = [getdate(upto or nowdate())]
    if item.actual_off_hire_date:
        end_candidates.append(getdate(item.actual_off_hire_date))
    elif not order.is_open_ended and (item.expected_off_hire_date
                                      or order.expected_to_date):
        end_candidates.append(getdate(item.expected_off_hire_date
                                      or order.expected_to_date))
    return start, min(end_candidates)


def expected_cost(item, order, upto=None, since=None):
    """Cost we expect the vendor to charge for a line up to a date."""
    start, end = item_charge_period(item, order, upto)
    if since:
        start = max(start, getdate(since))
    if end < start:
        return 0.0, 0.0
    units = get_billable_units(start, end, item.rate_basis, item.min_hire_units)
    amount = flt(units) * (flt(item.qty) or 1) * flt(item.rate)
    return flt(units, 4), flt(amount, 2)


def accrue_cross_hire_costs():
    """Nightly: refresh the accrued (incurred but not yet invoiced) hire cost."""
    if not get_settings().enable_cross_hire_accrual:
        return

    orders = frappe.get_all("Cross Hire Order",
                            filters={"docstatus": 1,
                                     "status": ["in", ["Ordered", "On Hire",
                                                       "Partially Off-Hired"]]},
                            pluck="name")
    for name in orders:
        try:
            order = frappe.get_doc("Cross Hire Order", name)
            total = 0.0
            for item in order.items:
                if item.item_status == "Cancelled":
                    continue
                _units, amount = expected_cost(item, order)
                item.db_set("accrued_amount", amount, update_modified=False)
                total += amount
            order.db_set("accrued_cost", flt(total, 2), update_modified=False)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(),
                             "Cross hire accrual failed: {0}".format(name))


# ------------------------------------------------------------------ leak alerts
def get_idle_cross_hired_units(min_days=None):
    """Units we are paying a vendor for that are not earning anything today."""
    settings = get_settings()
    min_days = int(min_days if min_days is not None else (settings.idle_alert_days or 3))
    cutoff = add_days(nowdate(), -min_days)

    rows = frappe.db.sql("""
        select e.name as equipment, e.equipment_name, e.status, e.cross_hire_order,
            i.name as order_row, i.rate, i.rate_basis, i.on_hire_date,
            o.supplier, o.company, o.cost_center
        from `tabRental Equipment` e
        inner join `tabCross Hire Order Item` i on i.rental_equipment = e.name
        inner join `tabCross Hire Order` o on o.name = i.parent
        where e.ownership = 'Cross-Hired'
            and i.item_status = 'On Hire'
            and o.docstatus = 1
            and i.on_hire_date <= %(cutoff)s
    """, {"cutoff": cutoff}, as_dict=True)

    idle = []
    for row in rows:
        engaged = frappe.db.sql("""
            select 1 from `tabRental Contract Item` ci
            inner join `tabRental Contract` c on c.name = ci.parent
            where ci.equipment = %(equipment)s and c.docstatus = 1
                and ci.item_status in ('Pending Dispatch', 'On Rent')
            limit 1""", {"equipment": row.equipment})
        if engaged:
            continue
        last_use = frappe.db.sql("""
            select max(coalesce(ci.off_rent_date, ci.charge_upto))
            from `tabRental Contract Item` ci
            inner join `tabRental Contract` c on c.name = ci.parent
            where ci.equipment = %(equipment)s and c.docstatus = 1""",
            {"equipment": row.equipment})
        since = (last_use and last_use[0][0]) or row.on_hire_date
        row["idle_since"] = since
        row["idle_days"] = frappe.utils.date_diff(nowdate(), since)
        row["idle_cost"] = _idle_cost(row["idle_days"], row.rate, row.rate_basis)
        if row["idle_days"] >= min_days:
            idle.append(row)
    return idle


def _idle_cost(days, rate, rate_basis):
    divisor = {"Hour": 1 / 24.0, "Day": 1, "Week": 7, "Month": 30}.get(rate_basis, 1)
    return flt(flt(days) / divisor * flt(rate), 2)


def alert_idle_cross_hire():
    for row in get_idle_cross_hired_units():
        _alert("Cross Hire Order", row.cross_hire_order,
               _("{0} has been idle for {1} days but is still on hire from {2} "
                 "(about {3} burnt)").format(row.equipment_name, row.idle_days,
                                             row.supplier, row.idle_cost))


def alert_off_hire_notice_due():
    """Warn before the vendor's notice period runs out."""
    today = getdate(nowdate())
    rows = frappe.db.sql("""
        select o.name, o.supplier, o.off_hire_notice_days, i.name as row_name,
            i.description, i.expected_off_hire_date
        from `tabCross Hire Order Item` i
        inner join `tabCross Hire Order` o on o.name = i.parent
        where o.docstatus = 1 and i.item_status = 'On Hire'
            and i.off_hire_notice_date is null
            and i.expected_off_hire_date is not null
    """, as_dict=True)
    for row in rows:
        notice_day = add_days(row.expected_off_hire_date,
                              -1 * int(row.off_hire_notice_days or 0))
        if getdate(notice_day) <= today:
            _alert("Cross Hire Order", row.name,
                   _("Give {0} off-hire notice for {1} - collection due {2}").format(
                       row.supplier, row.description or row.row_name,
                       row.expected_off_hire_date))


def alert_orphan_cross_hire():
    """The classic leak: the customer sent it back, the vendor never collected it."""
    rows = frappe.db.sql("""
        select o.name, o.supplier, i.description, i.rental_equipment,
            max(ci.off_rent_date) as returned_on
        from `tabCross Hire Order Item` i
        inner join `tabCross Hire Order` o on o.name = i.parent
        inner join `tabRental Contract Item` ci on ci.equipment = i.rental_equipment
        inner join `tabRental Contract` c on c.name = ci.parent and c.docstatus = 1
        where o.docstatus = 1 and i.item_status = 'On Hire'
            and ci.item_status = 'Returned'
        group by o.name, o.supplier, i.description, i.rental_equipment
    """, as_dict=True)
    for row in rows:
        _alert("Cross Hire Order", row.name,
               _("{0} came back from the customer on {1} but is still on hire "
                 "from {2}").format(row.description or row.rental_equipment,
                                    row.returned_on, row.supplier))


def _alert(doctype, name, subject):
    owner = frappe.db.get_value(doctype, name, "owner")
    if not owner or owner == "Administrator":
        return
    note = frappe.new_doc("Notification Log")
    note.subject = subject[:140]
    note.for_user = owner
    note.document_type = doctype
    note.document_name = name
    note.type = "Alert"
    note.insert(ignore_permissions=True)


# ------------------------------------------------------------------ margin
def get_unit_revenue(equipment, from_date=None, to_date=None):
    conditions = ["si.docstatus = 1", "sii.rental_equipment = %(equipment)s"]
    values = {"equipment": equipment}
    if from_date and to_date:
        conditions.append("si.posting_date between %(from_date)s and %(to_date)s")
        values.update({"from_date": from_date, "to_date": to_date})
    value = frappe.db.sql("""
        select sum(sii.base_net_amount)
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        where {conditions}""".format(conditions=" and ".join(conditions)), values)
    return flt(value[0][0]) if value and value[0][0] else 0.0
