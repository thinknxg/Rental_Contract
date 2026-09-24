import frappe


def set_property_setter(doctype, fieldname, prop, value, prop_type="Data"):
    filters = {"doc_type": doctype, "field_name": fieldname, "property": prop}
    if frappe.db.exists("Property Setter", filters):
        frappe.db.set_value("Property Setter", filters, "value", value)
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": doctype,
            "field_name": fieldname,
            "property": prop,
            "property_type": prop_type,
            "value": value,
            "doctype_or_field": "DocField",
        }).insert()


def execute():
    # Relabel Item Code -> Job No (functionality unchanged, still a real Link)
    set_property_setter("Sales Order Item", "item_code", "label", "Job No")

    # Show Item Name as a grid column, right after Job No
    set_property_setter("Sales Order Item", "item_name", "in_list_view", "1", "Check")
    set_property_setter("Sales Order Item", "item_name", "insert_after", "item_code")

    frappe.clear_cache(doctype="Sales Order Item")
    frappe.db.commit()
