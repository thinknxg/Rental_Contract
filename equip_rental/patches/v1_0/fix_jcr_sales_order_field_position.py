import frappe


def execute():
    if frappe.db.exists("Custom Field", "JCR-sales_order"):
        frappe.db.set_value("Custom Field", "JCR-sales_order", "insert_after", "naming_series")
    frappe.clear_cache(doctype="JCR")
