import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from equip_rental.utils.common import get_settings


class CrossHireReceipt(Document):
    def validate(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        if order.docstatus != 1:
            frappe.throw(_("The Cross Hire Order must be submitted"))
        self.company = self.company or order.company
        if getdate(self.receipt_datetime) < getdate(order.order_date):
            frappe.throw(_("The on-hire date cannot be before the order date"))

    def on_submit(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        on_hire_date = getdate(self.receipt_datetime)

        for row in self.items:
            item = self.get_order_item(order, row)
            item.db_set("on_hire_date", on_hire_date, update_modified=False)
            item.db_set("item_status", "On Hire", update_modified=False)
            item.db_set("meter_in", flt(row.meter_in), update_modified=False)
            if row.vendor_plant_no:
                item.db_set("vendor_plant_no", row.vendor_plant_no,
                            update_modified=False)

            if self.create_fleet_records and not item.rental_equipment:
                equipment = self.create_equipment(order, item, row)
                item.db_set("rental_equipment", equipment, update_modified=False)
                row.db_set("rental_equipment", equipment, update_modified=False)
            elif item.rental_equipment:
                self.reopen_equipment(order, item)

        order.reload()
        order.set_status_from_items()

    def get_order_item(self, order, row):
        for item in order.items:
            if row.order_row and item.name == row.order_row:
                return item
        for item in order.items:
            if (item.equipment_category == row.equipment_category
                    and item.item_status == "Ordered"):
                return item
        frappe.throw(_("Row {0}: no matching line on {1}").format(
            row.idx, self.cross_hire_order))

    def create_equipment(self, order, item, row):
        """A cross-hired unit becomes an ordinary fleet record for the hire period,
        so it can be dispatched, re-hired and invoiced like anything else."""
        settings = get_settings()
        equipment = frappe.new_doc("Rental Equipment")
        equipment.equipment_name = "{0}{1}".format(
            row.description or item.description or item.equipment_category,
            " [{0}]".format(row.vendor_plant_no) if row.vendor_plant_no else "")
        equipment.equipment_category = item.equipment_category
        equipment.company = order.company
        equipment.ownership = "Cross-Hired"
        equipment.supplier = order.supplier
        equipment.supplier_rate = item.rate
        equipment.cross_hire_rate_basis = item.rate_basis
        equipment.vendor_plant_no = row.vendor_plant_no
        equipment.cross_hire_order = order.name
        equipment.cross_hire_order_item = item.name
        equipment.hire_available_from = getdate(self.receipt_datetime)
        equipment.hire_available_upto = item.expected_off_hire_date \
            or order.expected_to_date
        equipment.current_location = self.location or settings.default_warehouse
        equipment.current_meter = flt(row.meter_in)
        equipment.status = "Available"
        equipment.item = frappe.db.get_value("Equipment Category",
                                             item.equipment_category, "default_item")
        equipment.flags.ignore_permissions = True
        equipment.insert()
        return equipment.name

    def reopen_equipment(self, order, item):
        frappe.db.set_value("Rental Equipment", item.rental_equipment, {
            "status": "Available",
            "hire_available_from": getdate(self.receipt_datetime),
            "hire_available_upto": item.expected_off_hire_date or order.expected_to_date,
        }, update_modified=False)

    def on_cancel(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        for row in self.items:
            item = self.get_order_item_by_row(order, row)
            if not item:
                continue
            item.db_set("item_status", "Ordered", update_modified=False)
            item.db_set("on_hire_date", None, update_modified=False)
            if item.rental_equipment:
                frappe.db.set_value("Rental Equipment", item.rental_equipment,
                                    "status", "Out of Service", update_modified=False)
        order.reload()
        order.set_status_from_items()

    def get_order_item_by_row(self, order, row):
        for item in order.items:
            if item.name == row.order_row:
                return item
        return None
