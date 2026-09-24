import frappe


def execute():
    hire_depends_on = 'eval:["Material Hire Order","Contract Hire Order"].includes(parent.custom_deal_type)'
    for fieldname in ("job_no", "contract_days"):
        frappe.db.set_value("Custom Field", f"Sales Order Item-{fieldname}", "depends_on", hire_depends_on)
    frappe.clear_cache(doctype="Sales Order Item")
