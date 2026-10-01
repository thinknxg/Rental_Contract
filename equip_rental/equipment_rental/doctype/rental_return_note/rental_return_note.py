# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RentalReturnNote(Document):
    def validate(self):
        if not self.rental_contract:
            frappe.throw(_("Sales Order is required"))
        so = frappe.get_cached_doc("Sales Order", self.rental_contract)
        self.company = self.company or so.company
        self.customer = so.customer

        total = 0.0
        for row in self.items:
            if row.item_code and not row.item_name:
                row.item_name = frappe.db.get_value("Item", row.item_code, "item_name")
            if row.item_code and not row.rate:
                row.rate = self.get_standard_rate(row.item_code)

            if not row.damage_amount:
                row.damage_amount = flt(row.damage_qty) * flt(row.rate)
            if not row.scrap_amount:
                row.scrap_amount = flt(row.scrap_qty) * flt(row.rate)
            if not row.lost_amount:
                row.lost_amount = flt(row.lost_qty) * flt(row.rate)

            row.charge_amount = flt(row.damage_amount) + flt(row.scrap_amount) + flt(row.lost_amount)
            total += flt(row.charge_amount)

        self.total_damage_charges = flt(total, 2)
        self.before_submit()
        self.validate_returnable()

    def validate_returnable(self):
        """Same rule as core Sales Return: cannot return more than was
        delivered, minus what has already been returned."""
        if not self.rental_dispatch_note:
            frappe.throw(_("Rental Dispatch Note is required"))
        original = frappe.db.get_value("Rental Dispatch Note", self.rental_dispatch_note, "delivery_note")
        if not original:
            frappe.throw(_("Dispatch Note {0} has no Delivery Note").format(self.rental_dispatch_note))
        remaining = {}
        for r in frappe.get_all("Delivery Note Item", filters={"parent": original},
                                fields=["item_code", "qty", "returned_qty"]):
            remaining[r.item_code] = remaining.get(r.item_code, 0) + flt(r.qty) - abs(flt(r.returned_qty))
        for row in self.items:
            if flt(row.qty_returned) > remaining.get(row.item_code, 0) + 0.000001:
                frappe.throw(_("Row {0}: cannot return more than {1} of {2}").format(
                    row.idx, remaining.get(row.item_code, 0), row.item_code))

    @staticmethod
    def get_standard_rate(item_code):
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "selling": 1, "price_list": frappe.db.get_single_value(
                "Selling Settings", "selling_price_list")},
            "price_list_rate",
        )
        if not price:
            price = frappe.db.get_value(
                "Item Price", {"item_code": item_code, "selling": 1}, "price_list_rate")
        return flt(price)

    def before_submit(self):
        invoiced = frappe.db.sql(
            """select si.name from `tabSales Invoice` si
               left join `tabSales Invoice Item` sii on sii.parent = si.name
               join `tabJCR` j on (j.name = si.jcr or j.name = sii.jcr)
               where si.docstatus = 1 and j.sales_order = %s limit 1""",
            self.rental_contract,
        )
        if not invoiced:
            frappe.throw(_("A submitted Sales Invoice (created from a JCR) for Sales Order {0} is required before this Return Note can be submitted").format(self.rental_contract))

    def on_submit(self):
        self.create_return_delivery_note()
        self.receive_non_good_returns()

    def on_cancel(self):
        for name in frappe.get_all("Stock Entry", filters={"docstatus": 1, "remarks": self.stock_entry_remarks()}, pluck="name"):
            se = frappe.get_doc("Stock Entry", name)
            se.flags.ignore_permissions = True
            se.cancel()
        if self.return_delivery_note:
            dn = frappe.get_doc("Delivery Note", self.return_delivery_note)
            if dn.docstatus == 1:
                dn.flags.ignore_permissions = True
                dn.cancel()

    def create_return_delivery_note(self):
        """Good returned quantities go back to stock through core's own
        return function, so the return is linked to the original Delivery
        Note (return_against) and delivered_qty on the Sales Order reverses.
        Damage/scrap/lost amounts are billing only and never touch stock."""
        from erpnext.controllers.sales_and_purchase_return import make_return_doc

        returned = {}
        for r in self.items:
            if flt(r.qty_returned) > 0:
                returned[r.item_code] = returned.get(r.item_code, 0) + flt(r.qty_returned)
        if not returned:
            return

        original = frappe.db.get_value("Rental Dispatch Note", self.rental_dispatch_note, "delivery_note")
        dn = make_return_doc("Delivery Note", original)
        kept = []
        for row in dn.items:
            qty = returned.get(row.item_code)
            if not qty:
                continue
            give = min(qty, abs(flt(row.qty)))
            row.qty = -give
            returned[row.item_code] -= give
            kept.append(row)
        dn.items = kept

        if not dn.items:
            frappe.throw(_("None of the returned items match the dispatched Delivery Note {0}").format(original))

        dn.flags.ignore_permissions = True
        dn.insert()
        dn.submit()
        self.db_set("return_delivery_note", dn.name)


    def stock_entry_remarks(self):
        return "Damaged / scrap / excess returns from {0}".format(self.name)

    def receive_non_good_returns(self):
        """Damaged, scrap and excess-returned quantities are physically
        with us, so they are received into their own warehouses.
        Lost quantity gets no stock entry."""
        abbr = frappe.get_cached_value("Company", self.company, "abbr")
        targets = (("damage_qty", "Damaged"), ("scrap_qty", "Scrap"), ("excess_qty", "Excess"))
        rows = []
        for row in self.items:
            for fieldname, wh in targets:
                qty = flt(row.get(fieldname))
                if qty <= 0:
                    continue
                warehouse = "{0} - {1}".format(wh, abbr)
                if not frappe.db.exists("Warehouse", warehouse):
                    frappe.throw(_("Warehouse {0} does not exist").format(warehouse))
                rate = flt(frappe.db.get_value(
                    "Bin", {"item_code": row.item_code, "warehouse": row.warehouse}, "valuation_rate")) or flt(row.rate)
                rows.append({
                    "item_code": row.item_code,
                    "qty": qty,
                    "t_warehouse": warehouse,
                    "basic_rate": rate,
                    "allow_zero_valuation_rate": 0 if rate else 1,
                })
        if not rows:
            return
        se = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "purpose": "Material Receipt",
            "company": self.company,
            "items": rows,
            "remarks": self.stock_entry_remarks(),
        })
        se.flags.ignore_permissions = True
        se.insert()
        se.submit()


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def item_condition(row):
        return flt(row.damage_qty) + flt(row.scrap_qty) + flt(row.lost_qty) > 0

    def update_item(source_row, target_row, source_parent):
        target_row.qty = flt(source_row.damage_qty) + flt(source_row.scrap_qty) + flt(source_row.lost_qty)
        target_row.rate = flt(source_row.charge_amount) / target_row.qty if target_row.qty else 0
        target_row.amount = flt(source_row.charge_amount)

    return get_mapped_doc("Rental Return Note", source_name, {
        "Rental Return Note": {
            "doctype": "Sales Invoice",
            "field_map": {"customer": "customer", "company": "company"},
            "validation": {"docstatus": ["=", 1]},
        },
        "Rental Return Note Item": {
            "doctype": "Sales Invoice Item",
            "condition": item_condition,
            "postprocess": update_item,
        },
    }, target_doc)
