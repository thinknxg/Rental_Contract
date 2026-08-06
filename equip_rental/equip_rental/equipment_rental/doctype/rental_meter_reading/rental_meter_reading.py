import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RentalMeterReading(Document):
    def validate(self):
        current = flt(frappe.db.get_value("Rental Equipment", self.equipment,
                                          "current_meter"))
        if flt(self.reading) < current:
            frappe.msgprint(
                _("Reading {0} is lower than the last recorded reading {1}").format(
                    self.reading, current), indicator="orange", alert=True)

    def on_update(self):
        current = flt(frappe.db.get_value("Rental Equipment", self.equipment,
                                          "current_meter"))
        if flt(self.reading) > current:
            frappe.db.set_value("Rental Equipment", self.equipment, "current_meter",
                                flt(self.reading), update_modified=False)
