# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class HireReturnNote(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        total = 0
        for item in self.items:
            item.total_qty = flt(item.good_qty) + flt(item.damage_qty)
            total += item.total_qty
        self.total_qty_to_return = total
