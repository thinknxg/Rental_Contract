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
            item.area = flt(item.length) * flt(item.width)
            item.contract_amount = flt(item.contract_rate) * flt(item.qty)

    def calculate_service_amounts(self):
        for service in self.services:
            service.amount = flt(service.rate) * flt(service.qty)

    def calculate_total(self):
        items_total = sum(flt(item.contract_amount) for item in self.items)
        services_total = sum(flt(service.amount) for service in self.services)
        self.total_contract_amount = items_total + services_total
