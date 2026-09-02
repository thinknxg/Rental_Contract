# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class HireReturnNote(Document):
    def validate(self):
        self.calculate_totals()

    def calculate_totals(self):
        self.total_qty_to_return_wh = sum(flt(i.qty_returned) for i in self.items)
        self.total_qty_to_return_cross_wh = sum(flt(i.excess_qty) for i in self.items)
        self.total_qty_to_return = self.total_qty_to_return_wh + self.total_qty_to_return_cross_wh
