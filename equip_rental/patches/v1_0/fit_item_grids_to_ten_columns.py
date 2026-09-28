import frappe

# Frappe's inline grid draws ~10 columns; extra ones are cut off from the
# right. Hide these from the grid (still available on the expanded row).
# Edit the lists to choose different columns.
HIDE = {
    "Quotation Item": ["item_name", "description", "period", "qty"],
    "Sales Order Item": ["item_name", "description", "period", "qty"],
}


def execute():
    for dt, fieldnames in HIDE.items():
        for fn in fieldnames:
            frappe.make_property_setter({
                "doctype": dt,
                "fieldname": fn,
                "property": "in_list_view",
                "value": "0",
                "property_type": "Check",
            })
        frappe.clear_cache(doctype=dt)
