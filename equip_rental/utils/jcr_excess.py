import frappe
from frappe.utils import flt, getdate


def calculate_excess(doc, method=None):
    for row in doc.get("items", []):
        row.excess_amount = _row_excess(row)


def _row_excess(row):
    if not (row.get("custom_erection_date") and row.get("custom_dismantle_date")):
        return 0

    erection = getdate(row.custom_erection_date)
    dismantle = getdate(row.custom_dismantle_date)
    actual_days = (dismantle - erection).days
    if actual_days <= 0:
        return 0

    contract_days = flt(row.get("contract_days"))
    excess_days = actual_days - contract_days
    if excess_days <= 0:
        return 0

    excess_charge = flt(row.get("excess_charge"))
    period = row.get("excess_period")

    if period == "Weekly":
        return (excess_days / 7) * excess_charge
    if period == "Monthly":
        return (excess_days / 30) * excess_charge
    return excess_days * excess_charge  # Days, or unset
