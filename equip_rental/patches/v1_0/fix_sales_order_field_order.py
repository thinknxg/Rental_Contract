import frappe


def execute():
    order = [
        ("customer", 5),
        ("customer_name", 6),
        ("column_break_7", 7),
        ("order_type", 8),
        ("custom_deal_type", 9),
    ]
    for fieldname, idx in order:
        frappe.db.set_value("Custom Field", f"Sales Order-{fieldname}", "idx", idx, update_modified=False)
    frappe.clear_cache(doctype="Sales Order")
