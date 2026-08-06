import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate


class RentalOffHireRequest(Document):
    def validate(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        if contract.docstatus != 1:
            frappe.throw(_("The rental contract must be submitted"))
        if getdate(self.requested_date) < getdate(contract.start_date):
            frappe.throw(_("The collection date cannot be before the contract start"))
        if self.equipment and self.equipment not in [i.equipment for i in contract.items]:
            frappe.throw(_("{0} is not on this contract").format(self.equipment))


@frappe.whitelist()
def make_return_note(source_name, target_doc=None):
    request = frappe.get_doc("Rental Off Hire Request", source_name)
    contract = frappe.get_doc("Rental Contract", request.rental_contract)

    note = frappe.new_doc("Rental Return Note")
    note.rental_contract = contract.name
    note.company = contract.company
    note.return_datetime = request.requested_date

    for item in contract.items:
        if item.item_status != "On Rent":
            continue
        if request.equipment and item.equipment != request.equipment:
            continue
        row = note.append("items", {})
        row.equipment = item.equipment
        row.equipment_name = item.equipment_name
        row.condition_in = "Good"

    if not note.items:
        frappe.throw(_("Nothing is on rent against this request"))
    return note
