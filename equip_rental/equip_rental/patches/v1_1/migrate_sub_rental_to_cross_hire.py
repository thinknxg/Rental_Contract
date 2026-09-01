"""Sub Rental Order was the v1.0 placeholder for hired-in equipment.
Cross Hire Order replaces it with a full hire-in lifecycle."""

import frappe


def execute():
    frappe.reload_doc("cross_hire", "doctype", "cross_hire_order")
    frappe.reload_doc("cross_hire", "doctype", "cross_hire_order_item")

    frappe.db.sql("""update `tabRental Equipment`
        set ownership = 'Cross-Hired' where ownership = 'Sub-Rented'""")

    if not frappe.db.table_exists("Sub Rental Order"):
        return

    for old in frappe.db.sql("""select * from `tabSub Rental Order`
            where docstatus < 2""", as_dict=True):
        if frappe.db.exists("Cross Hire Order", {"vendor_reference": old.name}):
            continue

        order = frappe.new_doc("Cross Hire Order")
        order.supplier = old.supplier
        order.company = old.company
        order.currency = old.currency
        order.order_date = old.from_date
        order.from_date = old.from_date
        order.expected_to_date = old.to_date
        order.rental_contract = old.rental_contract
        order.hire_purpose = "Re-Hire to Customer" if old.rental_contract \
            else "Internal Project Use"
        order.vendor_reference = old.name
        order.delivery_address = old.delivery_address
        order.remarks = old.remarks

        for item in frappe.db.sql("""select * from `tabSub Rental Order Item`
                where parent = %s order by idx""", old.name, as_dict=True):
            row = order.append("items", {})
            row.equipment_category = frappe.db.get_value(
                "Rental Equipment", item.equipment, "equipment_category")
            row.description = item.description
            row.qty = item.qty
            row.rate_basis = item.rate_basis
            row.rate = item.rate
            row.expected_from_date = old.from_date
            row.expected_off_hire_date = old.to_date
            row.rental_equipment = item.equipment

        if not order.items:
            continue

        order.flags.ignore_permissions = True
        order.flags.ignore_mandatory = True
        order.insert()
        if old.docstatus == 1:
            order.submit()

    frappe.delete_doc("DocType", "Sub Rental Order", force=1, ignore_missing=True)
    frappe.delete_doc("DocType", "Sub Rental Order Item", force=1, ignore_missing=True)
    frappe.db.commit()
