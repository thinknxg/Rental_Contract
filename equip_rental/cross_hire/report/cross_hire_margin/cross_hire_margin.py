import frappe
from frappe import _
from frappe.utils import flt

from equip_rental.utils.cross_hire import get_unit_revenue


def execute(filters=None):
    filters = frappe._dict(filters or {})
    conditions = ["o.docstatus = 1"]
    if filters.supplier:
        conditions.append("o.supplier = %(supplier)s")
    if filters.customer:
        conditions.append("o.customer = %(customer)s")

    lines = frappe.db.sql("""
        select o.name as cross_hire_order, o.supplier, o.customer, o.rental_contract,
            o.hire_purpose, i.description, i.rental_equipment, i.accrued_amount,
            i.invoiced_amount, i.damage_charged, i.transport_in, i.transport_out
        from `tabCross Hire Order Item` i
        inner join `tabCross Hire Order` o on o.name = i.parent
        where {conditions}
    """.format(conditions=" and ".join(conditions)), filters, as_dict=True)

    rows = []
    for line in lines:
        cost = (flt(line.invoiced_amount) or flt(line.accrued_amount)) \
            + flt(line.transport_in) + flt(line.transport_out) \
            + flt(line.damage_charged)
        revenue = get_unit_revenue(line.rental_equipment, filters.from_date,
                                   filters.to_date) if line.rental_equipment else 0.0
        margin = flt(revenue - cost, 2)
        rows.append({
            "cross_hire_order": line.cross_hire_order,
            "supplier": line.supplier,
            "description": line.description,
            "rental_equipment": line.rental_equipment,
            "customer": line.customer,
            "rental_contract": line.rental_contract,
            "hire_purpose": line.hire_purpose,
            "cost": flt(cost, 2),
            "revenue": flt(revenue, 2),
            "margin": margin,
            "margin_percent": flt(margin * 100.0 / revenue, 1) if revenue else 0.0,
        })

    columns = [
        {"fieldname": "cross_hire_order", "label": _("Order"), "fieldtype": "Link",
         "options": "Cross Hire Order", "width": 130},
        {"fieldname": "supplier", "label": _("Vendor"), "fieldtype": "Link",
         "options": "Supplier", "width": 150},
        {"fieldname": "description", "label": _("Equipment"), "fieldtype": "Data",
         "width": 170},
        {"fieldname": "rental_equipment", "label": _("Fleet Record"),
         "fieldtype": "Link", "options": "Rental Equipment", "width": 120},
        {"fieldname": "hire_purpose", "label": _("Purpose"), "fieldtype": "Data",
         "width": 140},
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link",
         "options": "Customer", "width": 150},
        {"fieldname": "rental_contract", "label": _("Contract"), "fieldtype": "Link",
         "options": "Rental Contract", "width": 130},
        {"fieldname": "cost", "label": _("Hire Cost"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "revenue", "label": _("Re-Hire Revenue"), "fieldtype": "Currency",
         "width": 140},
        {"fieldname": "margin", "label": _("Margin"), "fieldtype": "Currency",
         "width": 120},
        {"fieldname": "margin_percent", "label": _("Margin %"), "fieldtype": "Percent",
         "width": 100},
    ]

    summary = [
        {"label": _("Hire Cost"), "value": sum(r["cost"] for r in rows),
         "datatype": "Currency", "indicator": "Red"},
        {"label": _("Revenue"), "value": sum(r["revenue"] for r in rows),
         "datatype": "Currency", "indicator": "Blue"},
        {"label": _("Margin"), "value": sum(r["margin"] for r in rows),
         "datatype": "Currency", "indicator": "Green"},
    ]
    return columns, rows, None, None, summary
