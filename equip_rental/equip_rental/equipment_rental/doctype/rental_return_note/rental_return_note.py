import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class RentalReturnNote(Document):
    def validate(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        self.company = self.company or contract.company
        on_contract = {row.equipment: row for row in contract.items}

        total = 0.0
        for row in self.items:
            if row.equipment not in on_contract:
                frappe.throw(_("Row {0}: {1} is not on contract {2}").format(
                    row.idx, row.equipment, self.rental_contract))
            item = on_contract[row.equipment]
            if row.meter_in:
                row.meter_used = flt(row.meter_in) - flt(item.meter_out)
                if row.meter_used < 0:
                    frappe.throw(_("Row {0}: Meter In is lower than Meter Out").format(
                        row.idx))
            if row.condition_in in ("Damaged", "Not Working") and not row.damage_notes:
                frappe.throw(_("Row {0}: describe the damage").format(row.idx))
            total += flt(row.damage_charge) + flt(row.cleaning_charge) + flt(row.fuel_charge)

        self.total_damage_charges = flt(total, 2)

    def on_submit(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        return_date = getdate(self.return_datetime)

        for row in self.items:
            for item in contract.items:
                if item.equipment != row.equipment:
                    continue
                item.db_set("item_status", "Returned", update_modified=False)
                item.db_set("off_rent_date", return_date, update_modified=False)
                item.db_set("meter_in", flt(row.meter_in), update_modified=False)

            equipment = frappe.get_doc("Rental Equipment", row.equipment)
            if row.send_to_maintenance or row.condition_in in ("Damaged", "Not Working"):
                equipment.set_status("In Maintenance", contract=None)
                self.raise_maintenance(row)
            else:
                equipment.set_status("Available", contract=None)
            if row.meter_in:
                self.log_meter(row.equipment, row.meter_in)

        if self.add_charges_to_contract and self.total_damage_charges:
            self.append_charges(contract)

        if self.close_contract:
            contract.reload()
            contract.db_set("actual_end_date", return_date)
            contract.db_set("status", "Closed")
        else:
            contract.reload()
            contract.set_status(update=True)

    def append_charges(self, contract):
        contract.reload()
        for row in self.items:
            mapping = (("Damage Recovery", row.damage_charge, row.damage_notes),
                       ("Cleaning", row.cleaning_charge, None),
                       ("Fuel", row.fuel_charge, None))
            for charge_type, amount, note in mapping:
                if not flt(amount):
                    continue
                if not frappe.db.exists("Rental Charge Type", charge_type):
                    continue
                charge = contract.append("charges", {})
                charge.charge_type = charge_type
                charge.item = frappe.db.get_value("Rental Charge Type", charge_type, "item")
                charge.amount = flt(amount)
                charge.description = "{0} - {1} ({2})".format(
                    charge_type, row.equipment, note or self.name)
        contract.flags.ignore_validate_update_after_submit = True
        contract.save(ignore_permissions=True)

    def raise_maintenance(self, row):
        log = frappe.new_doc("Rental Maintenance Log")
        log.equipment = row.equipment
        log.maintenance_type = "Breakdown Repair"
        log.company = self.company
        log.from_datetime = self.return_datetime
        log.status = "Open"
        log.issue = row.damage_notes or _("Raised on return {0}").format(self.name)
        log.rental_contract = self.rental_contract
        log.meter_reading = flt(row.meter_in)
        log.flags.ignore_permissions = True
        log.insert()

    def log_meter(self, equipment, reading):
        doc = frappe.new_doc("Rental Meter Reading")
        doc.equipment = equipment
        doc.reading_datetime = self.return_datetime
        doc.reading = reading
        doc.source = "Return"
        doc.rental_contract = self.rental_contract
        doc.flags.ignore_permissions = True
        doc.insert()

    def on_cancel(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        for row in self.items:
            for item in contract.items:
                if item.equipment == row.equipment and item.item_status == "Returned":
                    item.db_set("item_status", "On Rent", update_modified=False)
                    item.db_set("off_rent_date", None, update_modified=False)
            frappe.get_doc("Rental Equipment", row.equipment).set_status(
                "On Rent", contract=self.rental_contract)
