# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RentalDispatchNote(Document):
    def validate(self):
        so = frappe.get_cached_doc("Sales Order", self.rental_contract)
        if so.docstatus != 1:
            frappe.throw(_("Sales Order {0} must be submitted").format(self.rental_contract))
        self.company = self.company or so.company
        self.customer = so.customer
        for row in self.items:
            if row.item_code and not row.item_name:
                row.item_name = frappe.db.get_value("Item", row.item_code, "item_name")
            row.amount = flt(row.qty) * flt(row.rate)

    def on_submit(self):
        self.create_delivery_note()

    def on_cancel(self):
        if self.delivery_note:
            dn = frappe.get_doc("Delivery Note", self.delivery_note)
            if dn.docstatus == 1:
                dn.flags.ignore_permissions = True
                dn.cancel()

    def create_delivery_note(self):
        from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

        dn = make_delivery_note(self.rental_contract)

        wanted = {}
        for row in self.items:
            wanted[row.item_code] = wanted.get(row.item_code, 0) + flt(row.qty)

        kept = []
        for dn_row in dn.items:
            qty_here = wanted.get(dn_row.item_code)
            if not qty_here:
                continue
            dn_row.qty = min(flt(dn_row.qty), qty_here)
            wanted[dn_row.item_code] -= dn_row.qty
            kept.append(dn_row)
        dn.items = kept

        if not dn.items:
            frappe.throw(_("None of this note's items matched undelivered lines on {0}").format(self.rental_contract))

        for row in self.items:
            if row.warehouse:
                for dn_row in dn.items:
                    if dn_row.item_code == row.item_code and not dn_row.get("warehouse"):
                        dn_row.warehouse = row.warehouse

        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()
        self.db_set("delivery_note", dn.name)
