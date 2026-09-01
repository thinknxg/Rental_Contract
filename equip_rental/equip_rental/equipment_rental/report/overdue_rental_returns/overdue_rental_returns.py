import frappe
from frappe import _
from frappe.utils import date_diff, nowdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = ["c.docstatus = 1", "c.status not in ('Closed', 'Cancelled')",
                  "c.is_open_ended = 0", "i.item_status = 'On Rent'",
                  "c.expected_end_date < %(today)s"]
    if filters.company:
        conditions.append("c.company = %(company)s")
    if filters.customer:
        conditions.append("c.customer = %(customer)s")

    values = dict(filters)
    values["today"] = nowdate()

    rows = frappe.db.sql("""
        select c.name as contract, c.customer, c.customer_name, c.contract_type,
            c.expected_end_date, i.equipment, i.equipment_name, i.rate, i.rate_basis,
            c.currency
        from `tabRental Contract Item` i
        inner join `tabRental Contract` c on c.name = i.parent
        where {conditions}
        order by c.expected_end_date asc
    """.format(conditions=" and ".join(conditions)), values, as_dict=True)

    for row in rows:
        row["days_overdue"] = date_diff(nowdate(), row["expected_end_date"])

    columns = [
        {"fieldname": "contract", "label": _("Contract"), "fieldtype": "Link",
         "options": "Rental Contract", "width": 140},
        {"fieldname": "customer_name", "label": _("Customer"), "fieldtype": "Data",
         "width": 180},
        {"fieldname": "contract_type", "label": _("Type"), "fieldtype": "Data",
         "width": 120},
        {"fieldname": "equipment", "label": _("Equipment"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 130},
        {"fieldname": "equipment_name", "label": _("Name"), "fieldtype": "Data",
         "width": 170},
        {"fieldname": "expected_end_date", "label": _("Due On"), "fieldtype": "Date",
         "width": 110},
        {"fieldname": "days_overdue", "label": _("Days Overdue"), "fieldtype": "Int",
         "width": 120},
        {"fieldname": "rate", "label": _("Rate"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "rate_basis", "label": _("Basis"), "fieldtype": "Data",
         "width": 90},
    ]
    return columns, rows
