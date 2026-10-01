import frappe


def execute():
    for dt in ("Rental Dispatch Note", "Rental Return Note"):
        if frappe.db.has_column(dt, "sales_order") and frappe.db.has_column(dt, "rental_contract"):
            frappe.db.sql(
                f"update `tab{dt}` set rental_contract = sales_order "
                "where sales_order is not null and sales_order != ''"
            )
