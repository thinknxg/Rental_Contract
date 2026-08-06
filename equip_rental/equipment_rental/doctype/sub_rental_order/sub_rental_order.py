import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from equip_rental.utils.pricing import get_billable_units


class SubRentalOrder(Document):
    def validate(self):
        total = 0.0
        for row in self.items:
            if not row.units:
                row.units = get_billable_units(self.from_date, self.to_date,
                                               row.rate_basis, 1)
            row.amount = flt(row.units) * (flt(row.qty) or 1) * flt(row.rate)
            total += row.amount
        self.total_amount = flt(total, 2)

    def on_submit(self):
        self.db_set("status", "Ordered")
        for row in self.items:
            if row.equipment:
                frappe.db.set_value("Rental Equipment", row.equipment,
                                    {"ownership": "Sub-Rented", "supplier": self.supplier},
                                    update_modified=False)

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    @frappe.whitelist()
    def make_purchase_invoice(self):
        if self.purchase_invoice:
            frappe.throw(_("Purchase Invoice {0} already exists").format(
                self.purchase_invoice))

        invoice = frappe.new_doc("Purchase Invoice")
        invoice.supplier = self.supplier
        invoice.company = self.company
        invoice.currency = self.currency
        invoice.sub_rental_order = self.name

        for row in self.items:
            if not row.item:
                frappe.throw(_("Row {0}: set an Item to invoice against").format(row.idx))
            line = invoice.append("items", {})
            line.item_code = row.item
            line.qty = flt(row.units) * (flt(row.qty) or 1)
            line.rate = flt(row.rate)
            line.description = "{0} ({1} to {2})".format(
                row.description or row.equipment or row.item, self.from_date, self.to_date)

        invoice.set_missing_values()
        invoice.flags.ignore_permissions = True
        invoice.insert()
        self.db_set("purchase_invoice", invoice.name)
        self.db_set("status", "Invoiced")
        return invoice.name
