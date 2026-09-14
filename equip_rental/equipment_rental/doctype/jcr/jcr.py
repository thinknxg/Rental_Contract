# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JCR(Document):
    pass


@frappe.whitelist()
def make_sdv(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.jcr = source.name
        target.naming_series = "SDV-.#####"

    def update_item(source_row, target_row, source_parent):
        target_row.job_no = source_row.job_no
        target_row.description = source_row.job_description

    return get_mapped_doc("JCR", source_name, {
        "JCR": {
            "doctype": "SDV",
            "field_map": {"client_name": "customer"},
            "validation": {"docstatus": ["=", 1]},
        },
        "JCR Item": {
            "doctype": "SDV Item",
            "postprocess": update_item,
        },
    }, target_doc, post_process)
