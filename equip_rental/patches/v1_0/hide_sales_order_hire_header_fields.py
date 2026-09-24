import frappe


def execute():
    fields_to_hide = [
        "site_and_project", "section_break_hire_terms", "payment_terms_code", "payment_terms",
        "column_break_hire_lpo", "revision_no", "lpo_no", "lpo_date", "update_lpo_in_deliveries",
        "section_break_hire_dates", "contract_from", "contract_to", "column_break_hire_rent",
        "rent_start_from", "description_2", "services", "custom_hire_order",
        "custom_hire_order_contract", "section_break_hire", "custom_status", "status_date",
        "column_break_hire_hdr",
    ]
    for fieldname in fields_to_hide:
        frappe.db.set_value("Custom Field", f"Sales Order-{fieldname}", "hidden", 1)
    frappe.clear_cache(doctype="Sales Order")
