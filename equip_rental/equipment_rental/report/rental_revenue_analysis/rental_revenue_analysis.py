import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})

    conditions = ["si.docstatus = 1",
                  "si.posting_date between %(from_date)s and %(to_date)s",
                  "si.rental_contract is not null"]
    if filters.customer:
        conditions.append("si.customer = %(customer)s")
    if filters.equipment_category:
        conditions.append("eq.equipment_category = %(equipment_category)s")

    rows = frappe.db.sql("""
        select si.name as invoice, si.posting_date, si.customer, si.rental_contract,
            sii.rental_equipment as equipment, eq.equipment_category,
            sii.qty, sii.rate, sii.base_net_amount as amount, si.status,
            si.outstanding_amount
        from `tabSales Invoice Item` sii
        inner join `tabSales Invoice` si on si.name = sii.parent
        left join `tabRental Equipment` eq on eq.name = sii.rental_equipment
        where {conditions}
        order by si.posting_date desc
    """.format(conditions=" and ".join(conditions)), filters, as_dict=True)

    columns = [
        {"fieldname": "posting_date", "label": _("Date"), "fieldtype": "Date",
         "width": 100},
        {"fieldname": "invoice", "label": _("Invoice"), "fieldtype": "Link",
         "options": "Sales Invoice", "width": 140},
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link",
         "options": "Customer", "width": 160},
        {"fieldname": "rental_contract", "label": _("Contract"), "fieldtype": "Link",
         "options": "Rental Contract", "width": 140},
        {"fieldname": "equipment", "label": _("Equipment"), "fieldtype": "Link",
         "options": "Rental Equipment", "width": 130},
        {"fieldname": "equipment_category", "label": _("Category"), "fieldtype": "Link",
         "options": "Equipment Category", "width": 130},
        {"fieldname": "qty", "label": _("Units"), "fieldtype": "Float", "width": 90},
        {"fieldname": "rate", "label": _("Rate"), "fieldtype": "Currency", "width": 110},
        {"fieldname": "amount", "label": _("Amount"), "fieldtype": "Currency",
         "width": 130},
        {"fieldname": "outstanding_amount", "label": _("Outstanding"),
         "fieldtype": "Currency", "width": 130},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100},
    ]
    return columns, rows
