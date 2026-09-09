# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SDV(Document):
    def validate(self):
        self.calculate_areas()
        self.calculate_amounts()

    def calculate_areas(self):
        for item in self.items:
            item.area = flt(item.length) * flt(item.width)

    def calculate_amounts(self):
        # ASSUMPTION pending TL confirmation: Daily/Weekly/Monthly rate_type all bill
        # as rate_per_sqm x area x qty; only "Lumpsum" is a flat rate x qty.
        for item in self.items:
            if not item.job_type:
                continue
            job_type = frappe.get_cached_doc("Job Type", item.job_type)
            item.rate_type = job_type.rate_type
            if job_type.rate_type == "Lumpsum":
                item.rate = flt(job_type.lumpsum_rate)
                item.amount = flt(item.rate) * flt(item.qty)
            else:
                item.rate = flt(job_type.rate_per_sqm)
                item.amount = flt(item.rate) * flt(item.area) * flt(item.qty)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def update_item(source_row, target_row, source_parent):
        target_row.item_code = source_row.item_code
        target_row.item_name = source_row.description
        target_row.description = source_row.description
        target_row.qty = source_row.qty
        target_row.rate = source_row.rate
        target_row.amount = source_row.amount

    return get_mapped_doc("SDV", source_name, {
        "SDV": {
            "doctype": "Sales Invoice",
            "field_map": {"customer": "customer"},
            "validation": {"docstatus": ["=", 1]},
        },
        "SDV Item": {
            "doctype": "Sales Invoice Item",
            "postprocess": update_item,
        },
    }, target_doc)
