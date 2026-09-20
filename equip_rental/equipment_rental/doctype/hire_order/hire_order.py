# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class HireOrder(Document):
    def validate(self):
        self.calculate_item_amounts()
        self.calculate_service_amounts()
        self.calculate_total()

    def calculate_item_amounts(self):
        for item in self.items:
            item.area = flt(item.length) * flt(item.width) * flt(item.height)
            item.contract_amount = flt(item.contract_rate) * flt(item.qty)

    def calculate_service_amounts(self):
        for service in self.services:
            service.amount = flt(service.rate) * flt(service.qty)

    def calculate_total(self):
        items_total = sum(flt(item.contract_amount) for item in self.items)
        services_total = sum(flt(service.amount) for service in self.services)
        self.total_contract_amount = items_total + services_total


@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def set_missing_values(source, target):
        target.customer = source.customer
        target.custom_deal_type = "Material Hire Order"

    def update_item(source, target, source_parent):
        target.item_name = source.description
        target.item_code = "TEST"
        target.description = source.description
        target.qty = source.qty
        target.rate = source.contract_rate
        target.amount = source.contract_amount

    return get_mapped_doc(
        "Hire Order",
        source_name,
        {
            "Hire Order": {
                "doctype": "Sales Order",
                "field_map": {},
            },
            "Hire Order Item": {
                "doctype": "Sales Order Item",
                "postprocess": update_item,
                "condition": lambda item: item.description,
            },
        },
        target_doc,
        set_missing_values,
    )
