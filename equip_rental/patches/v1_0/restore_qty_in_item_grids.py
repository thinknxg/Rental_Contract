import frappe


def execute():
    # Bring Qty back into the Items grids on Quotation and Sales Order
    for dt in ("Quotation Item", "Sales Order Item"):
        for prop, value, ptype in (("in_list_view", "1", "Check"), ("columns", "1", "Int")):
            frappe.make_property_setter({
                "doctype": dt,
                "fieldname": "qty",
                "property": prop,
                "value": value,
                "property_type": ptype,
            })
        frappe.clear_cache(doctype=dt)
