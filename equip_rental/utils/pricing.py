import calendar
import math

import frappe
from frappe import _
from frappe.utils import add_days, add_months, date_diff, flt, getdate

RATE_FIELD = {
    "Hour": "hourly_rate",
    "Day": "daily_rate",
    "Week": "weekly_rate",
    "Month": "monthly_rate",
}


def days_in_month(date):
    date = getdate(date)
    return calendar.monthrange(date.year, date.month)[1]


def get_billable_units(from_date, to_date, rate_basis, min_billable_units=1):
    """Number of chargeable units between two inclusive dates.

    Hour / Day  -> whole units (a part day is a full day, the industry norm)
    Week / Month-> pro-rated so part periods are charged fairly
    """
    from_date, to_date = getdate(from_date), getdate(to_date)
    if to_date < from_date:
        return 0.0

    days = date_diff(to_date, from_date) + 1

    if rate_basis == "Hour":
        units = days * 24.0
    elif rate_basis == "Day":
        units = float(days)
    elif rate_basis == "Week":
        units = round(days / 7.0, 2)
    elif rate_basis == "Month":
        months = 0
        cursor = from_date
        boundary = add_days(to_date, 1)
        while getdate(add_months(cursor, 1)) <= getdate(boundary):
            cursor = getdate(add_months(cursor, 1))
            months += 1
        remainder = date_diff(boundary, cursor)
        if remainder > 0:
            months += remainder / float(days_in_month(cursor))
        units = round(months, 4)
    else:
        frappe.throw(_("Unknown rate basis {0}").format(rate_basis))

    return flt(max(units, flt(min_billable_units) or 0), 4)


def get_rate_from_card(rate_card, rate_basis):
    if not rate_card:
        return None, None
    for row in frappe.get_all(
            "Rental Rate Card Line",
            filters={"parent": rate_card, "rate_basis": rate_basis},
            fields=["rate", "min_billable_units", "discount_percent"],
            order_by="idx asc", limit=1):
        return flt(row.rate), row
    return None, None


def get_rate(equipment, rate_basis, customer=None, date=None):
    """Rate resolution order: customer rate card -> equipment rate card ->
    equipment own rate -> category rate card."""
    doc = frappe.get_cached_doc("Rental Equipment", equipment)

    cards = []
    if customer:
        cards.append(frappe.db.get_value("Customer", customer, "default_rate_card"))
    cards.append(doc.rate_card)
    cards.append(frappe.db.get_value(
        "Equipment Category", doc.equipment_category, "default_rate_card"))

    for card in cards:
        if not card:
            continue
        rate, row = get_rate_from_card(card, rate_basis)
        if rate:
            return rate, row

    own = flt(doc.get(RATE_FIELD.get(rate_basis, "daily_rate")))
    if own:
        return own, None

    return 0.0, None


def get_display_rate(equipment):
    """Jinja helper: best rate to show on the public catalogue."""
    doc = frappe.get_cached_doc("Rental Equipment", equipment)
    for basis in ("Day", "Week", "Month", "Hour"):
        rate, _row = get_rate(doc.name, basis)
        if rate:
            return {"rate": rate, "basis": basis,
                    "currency": frappe.db.get_value(
                        "Company", doc.company, "default_currency")}
    return None


def line_amount(units, qty, rate, discount_percent=0):
    amount = flt(units) * (flt(qty) or 1) * flt(rate)
    if discount_percent:
        amount -= amount * flt(discount_percent) / 100.0
    return flt(amount, 2)


def next_billing_date(start_date, billing_cycle, calendar_month=True):
    start_date = getdate(start_date)
    if billing_cycle == "Daily":
        return add_days(start_date, 1)
    if billing_cycle == "Weekly":
        return add_days(start_date, 7)
    if billing_cycle == "Monthly":
        if calendar_month:
            first_next = getdate(add_months(start_date.replace(day=1), 1))
            return first_next
        return getdate(add_months(start_date, 1))
    return None


def period_end_for_cycle(period_start, billing_cycle, calendar_month=True):
    period_start = getdate(period_start)
    if billing_cycle == "Daily":
        return period_start
    if billing_cycle == "Weekly":
        return add_days(period_start, 6)
    if billing_cycle == "Monthly":
        if calendar_month:
            return add_days(getdate(add_months(period_start.replace(day=1), 1)), -1)
        return add_days(getdate(add_months(period_start, 1)), -1)
    return None
