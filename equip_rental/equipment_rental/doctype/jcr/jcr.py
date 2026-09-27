# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class JCR(Document):
    def validate(self):
        self.calculate_excess_amounts()

    def calculate_excess_amounts(self):
        # Mirrors the excess-period logic in jcr.js: Weekly = charge x (days / 7),
        # Monthly = charge x (days / 30), Days = charge x days.
        for item in self.items:
            excess_charge = flt(item.excess_charge)
            excess_days = flt(item.contract_days)
            if not excess_charge or not excess_days:
                item.excess_amount = 0
                continue
            if item.excess_period == "Weekly":
                item.excess_amount = (excess_days / 7) * excess_charge
            elif item.excess_period == "Monthly":
                item.excess_amount = (excess_days / 30) * excess_charge
            else:
                item.excess_amount = excess_days * excess_charge


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


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.ignore_pricing_rule = 1

    def update_item(source_row, target_row, source_parent):
        base_rate, base_amount, item_code, item_name = (0, 0, None, None)
        if source_row.sales_order_item:
            so_row = frappe.db.get_value(
                "Sales Order Item", source_row.sales_order_item,
                ["item_code", "item_name", "rate", "amount"], as_dict=True,
            )
            if so_row:
                item_code = so_row.item_code
                item_name = so_row.item_name
                base_rate = flt(so_row.rate)
                base_amount = flt(so_row.amount)

        target_row.item_code = item_code
        target_row.item_name = item_name or source_row.job_description
        target_row.description = source_row.job_description
        target_row.qty = source_row.qty or 1
        excess_amount = flt(source_row.excess_amount)
        target_row.amount = base_amount + excess_amount
        target_row.rate = target_row.amount / target_row.qty if target_row.qty else 0
        target_row.price_list_rate = target_row.rate
        target_row.base_rate = target_row.rate
        target_row.base_amount = target_row.amount
        target_row.ignore_pricing_rule = 1
        target_row.custom_locked_rate = target_row.rate
        target_row.custom_locked_amount = target_row.amount

    return get_mapped_doc("JCR", source_name, {
        "JCR": {
            "doctype": "Sales Invoice",
            "field_map": {"client_name": "customer"},
            "validation": {"docstatus": ["=", 1]},
        },
        "JCR Item": {
            "doctype": "Sales Invoice Item",
            "postprocess": update_item,
        },
    }, target_doc, post_process)


@frappe.whitelist()
def create_sales_invoice(source_name):
    # Builds the Sales Invoice via make_sales_invoice (same rate/amount logic,
    # proven correct server-side) and inserts it directly, instead of loading
    # it unsaved into the browser form. Loading an unsaved mapped doc lets
    # ERPNext's item_code change-trigger auto-refetch rate/tax from the
    # Item's default price, which overwrites our computed amount within a
    # second of the form rendering. Inserting server-side and only then
    # opening the saved record avoids that trigger firing at all.
    si = make_sales_invoice(source_name)
    si.insert()
    return si.name
