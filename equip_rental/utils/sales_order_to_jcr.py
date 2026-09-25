import html

import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import strip_html


@frappe.whitelist()
def make_jcr(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.hire_order = source.get("custom_hire_order")
        target.sales_order = source.name
        lpo_date = source.get("lpo_date")
        target.lpo_date = str(lpo_date) if lpo_date else None
        if not target.get("naming_series"):
            options = frappe.get_meta("JCR").get_field("naming_series").options or ""
            target.naming_series = options.split("\n")[0]

    def update_item(source_row, target_row, source_parent):
        target_row.job_no = source_row.get("job_no") or source_row.item_code
        target_row.sales_order_item = source_row.name
        target_row.contract_days = source_row.get("custom_contract_days")
        target_row.excess_charge = source_row.get("excess_charge")
        target_row.excess_period = source_row.get("excess_period")
        description = strip_html(source_row.description or "").strip()
        target_row.job_description = html.unescape(description) or source_row.item_name

    return get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "JCR",
                "field_map": {
                    "customer": "client_name",
                    "project": "project_name",
                    "lpo_no": "lpo_number",
                },
                "field_no_map": ["naming_series"],
                "validation": {"docstatus": ["=", 1]},
            },
            "Sales Order Item": {
                "doctype": "JCR Item",
                "postprocess": update_item,
            },
        },
        target_doc,
        set_missing_values,
    )
