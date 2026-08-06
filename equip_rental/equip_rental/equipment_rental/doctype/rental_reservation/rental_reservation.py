import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate

from equip_rental.utils.availability import is_available
from equip_rental.utils.pricing import get_rate


class RentalReservation(Document):
    def validate(self):
        if getdate(self.to_date) < getdate(self.from_date):
            frappe.throw(_("To Date cannot be before From Date"))
        for row in self.items:
            if row.equipment:
                if not row.equipment_category:
                    row.equipment_category = frappe.db.get_value(
                        "Rental Equipment", row.equipment, "equipment_category")
                row.is_available = 1 if is_available(
                    row.equipment, self.from_date, self.to_date,
                    ignore_reservation=self.name) else 0
                if not row.rate:
                    row.rate, _row = get_rate(row.equipment, row.rate_basis, self.customer)
            else:
                row.is_available = 0

    def on_update(self):
        if self.status == "Confirmed":
            for row in self.items:
                if row.equipment and not row.is_available:
                    frappe.throw(
                        _("Row {0}: {1} is not available for the requested period")
                        .format(row.idx, row.equipment))


@frappe.whitelist()
def make_rental_contract(source_name, target_doc=None):
    def post_process(source, target):
        target.contract_type = source.reservation_type
        target.start_date = source.from_date
        target.expected_end_date = source.to_date
        target.reservation = source.name
        target.run_method("set_missing_values")

    def item_condition(row):
        return bool(row.equipment)

    def update_item(source_row, target_row, source_parent):
        target_row.charge_from = source_parent.from_date
        target_row.charge_upto = source_parent.to_date

    doc = get_mapped_doc("Rental Reservation", source_name, {
        "Rental Reservation": {
            "doctype": "Rental Contract",
            "field_map": {"name": "reservation"},
            "validation": {"status": ["!=", "Converted"]},
        },
        "Rental Reservation Item": {
            "doctype": "Rental Contract Item",
            "field_map": {"equipment": "equipment", "rate_basis": "rate_basis",
                          "rate": "rate", "qty": "qty"},
            "condition": item_condition,
            "postprocess": update_item,
        },
    }, target_doc, post_process)
    return doc
