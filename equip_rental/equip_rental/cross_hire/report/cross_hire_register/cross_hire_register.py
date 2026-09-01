import frappe
from frappe import _
from frappe.utils import date_diff, flt, nowdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = ["o.docstatus = 1"]
    if filters.company:
        conditions.append("o.company = %(company)s")
    if filters.supplier:
        conditions.append("o.supplier = %(supplier)s")
    if filters.status:
        conditions.append("i.item_status = %(status)s")

    rows = frappe.db.sql("""
        select o.name as cross_hire_order, o.supplier, o.hire_purpose,
            o.rental_contract, o.project, i.description, i.vendor_plant_no,
            i.rental_equipment, i.rate, i.rate_basis, i.on_hire_date,
            i.expected_off_hire_date, i.actual_off_hire_date, i.item_status,
            i.accrued_amount, i.invoiced_amount, i.invoiced_upto, o.currency
        from `tabCross Hire Order Item` i
        inner join `tabCross Hire Order` o on o.name = i.parent
        where {conditions}
        order by i.on_hire_date asc
    """.format(conditions=" and ".join(conditions)), filters, as_dict=True)

    for row in rows:
        end = row.actual_off_hire_date or nowdate()
        row["days_on_hire"] = date_diff(end, row.on_hire_date) \
            if row.on_hire_date else 0
        row["uninvoiced"] = flt(row.accrued_amount) - flt(row.invoiced_amount)
        row["customer_contract"] = _current_contract(row.rental_equipment)

    columns = [
        {"fieldname": "cross_hire_order", "label": _("Order"), "fieldtype": "Link",
         "options": "Cross Hire Order", "width": 130},
        {"fieldname": "supplier", "label": _("Vendor"), "fieldtype": "Link",
         "options": "Supplier", "width": 150},
        {"fieldname": "description", "label": _("Equipment"), "fieldtype": "Data",
         "width": 170},
        {"fieldname": "vendor_plant_no", "label": _("Plant No"), "fieldtype": "Data",
         "width": 100},
        {"fieldname": "rental_equipment", "label": _("Fleet Record"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 120},
        {"fieldname": "item_status", "label": _("Status"), "fieldtype": "Data",
         "width": 130},
        {"fieldname": "on_hire_date", "label": _("On Hire"), "fieldtype": "Date",
         "width": 100},
        {"fieldname": "expected_off_hire_date", "label": _("Due Back"),
         "fieldtype": "Date", "width": 100},
        {"fieldname": "actual_off_hire_date", "label": _("Off Hired"),
         "fieldtype": "Date", "width": 100},
        {"fieldname": "days_on_hire", "label": _("Days"), "fieldtype": "Int",
         "width": 70},
        {"fieldname": "rate", "label": _("Rate"), "fieldtype": "Currency", "width": 100},
        {"fieldname": "rate_basis", "label": _("Basis"), "fieldtype": "Data",
         "width": 80},
        {"fieldname": "accrued_amount", "label": _("Accrued Cost"),
         "fieldtype": "Currency", "width": 120},
        {"fieldname": "invoiced_amount", "label": _("Vendor Invoiced"),
         "fieldtype": "Currency", "width": 130},
        {"fieldname": "uninvoiced", "label": _("Uninvoiced"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "customer_contract", "label": _("Deployed On"),
         "fieldtype": "Data", "width": 140},
        {"fieldname": "project", "label": _("Project"), "fieldtype": "Link",
         "options": "Project", "width": 120},
    ]
    return columns, rows


def _current_contract(equipment):
    if not equipment:
        return None
    row = frappe.db.sql("""
        select c.name from `tabRental Contract Item` ci
        inner join `tabRental Contract` c on c.name = ci.parent
        where ci.equipment = %s and c.docstatus = 1
            and ci.item_status in ('Pending Dispatch', 'On Rent') limit 1""", equipment)
    return row[0][0] if row else None
