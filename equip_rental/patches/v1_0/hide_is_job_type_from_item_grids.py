import frappe


def execute():
    # Hide the Is Job Type column from the Items grids. A Property Setter
    # is used so re-running earlier patches can't bring the column back.
    for dt in ("Quotation Item", "Sales Order Item"):
        frappe.make_property_setter({
            "doctype": dt,
            "fieldname": "is_job_type_item",
            "property": "in_list_view",
            "value": "0",
            "property_type": "Check",
        })
        frappe.clear_cache(doctype=dt)
