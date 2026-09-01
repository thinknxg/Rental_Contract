import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = ["r.docstatus < 2"]
    if filters.supplier:
        conditions.append("r.supplier = %(supplier)s")
    if filters.from_date:
        conditions.append("r.period_from >= %(from_date)s")
    if filters.to_date:
        conditions.append("r.period_to <= %(to_date)s")
    if filters.only_variances:
        conditions.append("abs(i.variance) > 0.01")

    rows = frappe.db.sql("""
        select r.name as reconciliation, r.supplier, r.vendor_invoice_no,
            r.cross_hire_order, r.status, i.description, i.charge_from, i.charge_upto,
            i.expected_units, i.expected_amount, i.claimed_units, i.claimed_amount,
            i.variance, i.decision, i.variance_reason
        from `tabCross Hire Reconciliation Item` i
        inner join `tabCross Hire Invoice Reconciliation` r on r.name = i.parent
        where {conditions}
        order by abs(i.variance) desc
    """.format(conditions=" and ".join(conditions)), filters, as_dict=True)

    columns = [
        {"fieldname": "reconciliation", "label": _("Reconciliation"),
         "fieldtype": "Link", "options": "Cross Hire Invoice Reconciliation",
         "width": 150},
        {"fieldname": "supplier", "label": _("Vendor"), "fieldtype": "Link",
         "options": "Supplier", "width": 150},
        {"fieldname": "vendor_invoice_no", "label": _("Vendor Invoice"),
         "fieldtype": "Data", "width": 130},
        {"fieldname": "description", "label": _("Line"), "fieldtype": "Data",
         "width": 170},
        {"fieldname": "charge_from", "label": _("From"), "fieldtype": "Date",
         "width": 100},
        {"fieldname": "charge_upto", "label": _("Upto"), "fieldtype": "Date",
         "width": 100},
        {"fieldname": "expected_amount", "label": _("Expected"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "claimed_amount", "label": _("Claimed"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "variance", "label": _("Variance"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "decision", "label": _("Decision"), "fieldtype": "Data",
         "width": 130},
        {"fieldname": "variance_reason", "label": _("Reason"), "fieldtype": "Data",
         "width": 220},
    ]
    return columns, rows
