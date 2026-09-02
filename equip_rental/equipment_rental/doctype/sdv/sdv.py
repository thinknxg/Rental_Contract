# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt


class SDV(Document):
    def validate(self):
        self.calculate_areas()

    def calculate_areas(self):
        for item in self.items:
            item.area = flt(item.length) * flt(item.width)
