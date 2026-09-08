import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class RentalReturnNote(Document):
    def validate(self):
        contract = frappe.get_cached_doc("Rental Contract", self.rental_contract)
        self.company = self.company or contract.company

        total = 0.0
        for row in self.items:
            row.rental_contract = contract.name
            row.project = contract.project
            row.warehouse = row.warehouse or contract.warehouse

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

    def on_submit(self):
        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        return_date = getdate(self.return_datetime)

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
        mapping = (
            ("Damage Recovery", "damage_amount"),
            ("Scrap Charge", "scrap_amount"),
            ("Lost Item Charge", "lost_amount"),
        )
        for row in self.items:
            for charge_type, fieldname in mapping:
                amount = flt(row.get(fieldname))
                if not amount:
                    continue
                if not frappe.db.exists("Rental Charge Type", charge_type):
                    continue
                charge = contract.append("charges", {})
                charge.charge_type = charge_type
                charge.item = frappe.db.get_value("Rental Charge Type", charge_type, "item")
                charge.amount = amount
                charge.description = "{0} - {1} ({2})".format(
                    charge_type, row.item_code, self.name)
        contract.flags.ignore_validate_update_after_submit = True
        contract.save(ignore_permissions=True)

    def on_cancel(self):
        pass


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def item_condition(row):
        return flt(row.damage_qty) + flt(row.scrap_qty) + flt(row.lost_qty) > 0

    def update_item(source_row, target_row, source_parent):
        target_row.qty = flt(source_row.damage_qty) + flt(source_row.scrap_qty) + flt(source_row.lost_qty)
        target_row.cost_center = frappe.get_cached_value(
            "Rental Contract", source_parent.rental_contract, "cost_center")

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
