import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class RentalDispatchNote(Document):
    def validate(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        if contract.docstatus != 1:
            frappe.throw(_("The rental contract must be submitted"))
        self.company = self.company or contract.company

        on_contract = {row.item for row in contract.items}
        for row in self.items:
            if row.item_code not in on_contract:
                frappe.throw(_("Row {0}: {1} is not on contract {2}").format(
                    row.idx, row.item_code, self.rental_contract))

    def get_contract_item(self, contract, row, used, status):
        for item in contract.items:
            if item.item == row.item_code and item.name not in used and item.item_status == status:
                return item
        return None

    def on_submit(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        internal = contract.contract_type == "Internal Use"
        dispatch_date = getdate(self.dispatch_datetime)
        used = set()

        for row in self.items:
            item = self.get_contract_item(contract, row, used, "Pending Dispatch")
            if not item:
                continue
            used.add(item.name)
            item.db_set("item_status", "On Rent", update_modified=False)
            if getdate(item.charge_from) < dispatch_date:
                item.db_set("charge_from", dispatch_date, update_modified=False)

            if item.equipment:
                equipment = frappe.get_doc("Rental Equipment", item.equipment)
                equipment.set_status("Internal Use" if internal else "On Rent",
                                     contract=self.rental_contract)

        contract.set_status(update=True)

    def on_cancel(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        used = set()
        for row in self.items:
            item = self.get_contract_item(contract, row, used, "On Rent")
            if not item:
                continue
            used.add(item.name)
            item.db_set("item_status", "Pending Dispatch", update_modified=False)
            if item.equipment:
                equipment = frappe.get_doc("Rental Equipment", item.equipment)
                equipment.set_status("Reserved", contract=self.rental_contract)
