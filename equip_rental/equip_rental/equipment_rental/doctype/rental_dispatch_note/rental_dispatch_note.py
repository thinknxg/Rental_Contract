import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class RentalDispatchNote(Document):
    def validate(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        if contract.docstatus != 1:
            frappe.throw(_("The rental contract must be submitted"))
        self.company = self.company or contract.company

        on_contract = {row.equipment: row for row in contract.items}
        for row in self.items:
            if row.equipment not in on_contract:
                frappe.throw(_("Row {0}: {1} is not on contract {2}").format(
                    row.idx, row.equipment, self.rental_contract))

    def on_submit(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        internal = contract.contract_type == "Internal Use"
        dispatch_date = getdate(self.dispatch_datetime)

        for row in self.items:
            for item in contract.items:
                if item.equipment != row.equipment:
                    continue
                item.db_set("item_status", "On Rent", update_modified=False)
                item.db_set("meter_out", flt(row.meter_out), update_modified=False)
                if getdate(item.charge_from) < dispatch_date:
                    item.db_set("charge_from", dispatch_date, update_modified=False)

            equipment = frappe.get_doc("Rental Equipment", row.equipment)
            equipment.set_status("Internal Use" if internal else "On Rent",
                                 contract=self.rental_contract)
            if row.meter_out:
                self.log_meter(row.equipment, row.meter_out)

        contract.set_status(update=True)

    def log_meter(self, equipment, reading):
        doc = frappe.new_doc("Rental Meter Reading")
        doc.equipment = equipment
        doc.reading_datetime = self.dispatch_datetime
        doc.reading = reading
        doc.source = "Dispatch"
        doc.rental_contract = self.rental_contract
        doc.flags.ignore_permissions = True
        doc.insert()

    def on_cancel(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        for row in self.items:
            for item in contract.items:
                if item.equipment == row.equipment and item.item_status == "On Rent":
                    item.db_set("item_status", "Pending Dispatch", update_modified=False)
            equipment = frappe.get_doc("Rental Equipment", row.equipment)
            equipment.set_status("Reserved", contract=self.rental_contract)
