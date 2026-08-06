import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate


class RentalMaintenanceLog(Document):
    def validate(self):
        if self.to_datetime and getdate(self.to_datetime) < getdate(self.from_datetime):
            frappe.throw(_("Available From cannot be before Down From"))

    def on_update(self):
        equipment = frappe.get_doc("Rental Equipment", self.equipment)

        if self.status in ("Open", "In Progress"):
            if equipment.status not in ("On Rent", "Internal Use"):
                equipment.set_status("In Maintenance", contract=equipment.current_contract)

        elif self.status == "Completed":
            if equipment.status == "In Maintenance":
                equipment.set_status("Available", contract=None)
            equipment.db_set("last_maintenance_date", getdate(
                self.to_datetime or self.from_datetime), update_modified=False)
            self.schedule_next(equipment)

        elif self.status == "Cancelled" and equipment.status == "In Maintenance":
            equipment.set_status("Available", contract=None)

    def schedule_next(self, equipment):
        category = frappe.get_cached_doc("Equipment Category", equipment.equipment_category)
        if category.maintenance_interval_days:
            equipment.db_set(
                "next_maintenance_date",
                add_days(getdate(self.to_datetime or self.from_datetime),
                         int(category.maintenance_interval_days)),
                update_modified=False)
        if category.maintenance_interval and self.meter_reading:
            equipment.db_set("next_maintenance_meter",
                             flt(self.meter_reading) + flt(category.maintenance_interval),
                             update_modified=False)
