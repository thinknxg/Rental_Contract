import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, nowdate

from equip_rental.utils.availability import validate_availability
from equip_rental.utils.common import get_billing_item, get_settings
from equip_rental.utils.pricing import (get_billable_units, get_rate, line_amount,
                                        next_billing_date)


class RentalContract(Document):
    def validate(self):
        self.set_missing_values()
        self.validate_dates()
        self.validate_items()
        self.calculate_totals()
        self.set_status()

    def set_missing_values(self):
        settings = get_settings()
        if not self.company:
            self.company = settings.default_company
        if not self.currency:
            self.currency = frappe.db.get_value("Company", self.company,
                                                "default_currency")
        if not self.billing_cycle:
            self.billing_cycle = settings.default_billing_cycle
        if not self.price_list and self.contract_type == "Customer Rental":
            self.price_list = (frappe.db.get_value("Customer", self.customer,
                                                   "default_price_list")
                               or settings.default_customer_price_list)
        if not self.taxes_and_charges and self.contract_type == "Customer Rental":
            self.taxes_and_charges = settings.default_taxes_and_charges
        if not self.cost_center:
            self.cost_center = frappe.db.get_value("Company", self.company,
                                                   "cost_center")
        if self.terms_template and not self.terms:
            self.terms = frappe.db.get_value("Terms and Conditions", self.terms_template,
                                             "terms")

    def validate_dates(self):
        if not self.is_open_ended and getdate(self.expected_end_date) < getdate(
                self.start_date):
            frappe.throw(_("Expected End Date cannot be before Start Date"))
        if self.actual_end_date and getdate(self.actual_end_date) < getdate(
                self.start_date):
            frappe.throw(_("Actual End Date cannot be before Start Date"))

    def validate_items(self):
        if not self.items:
            frappe.throw(_("Add at least one piece of equipment"))

        seen = {}
        for row in self.items:
            equipment = frappe.get_cached_doc("Rental Equipment", row.equipment)
            row.equipment_category = equipment.equipment_category
            row.equipment_name = equipment.equipment_name
            if not row.item:
                row.item = get_billing_item(equipment)
            if not row.charge_from:
                row.charge_from = self.start_date
            if not row.charge_upto and not self.is_open_ended:
                row.charge_upto = self.expected_end_date
            if not row.rate:
                row.rate, card_row = get_rate(row.equipment, row.rate_basis, self.customer)
                if card_row and not row.min_billable_units:
                    row.min_billable_units = card_row.get("min_billable_units")
            if not row.rate:
                frappe.throw(_("Row {0}: set a rate for {1}").format(row.idx,
                                                                     row.equipment))
            if row.equipment in seen:
                frappe.throw(_("Row {0}: {1} is listed more than once").format(
                    row.idx, row.equipment))
            seen[row.equipment] = row.idx

            if self.docstatus == 0 and row.item_status == "Pending Dispatch":
                validate_availability(row.equipment, row.charge_from,
                                      row.charge_upto or self.expected_end_date
                                      or row.charge_from,
                                      ignore_contract=self.name)

    def calculate_totals(self):
        total = 0.0
        for row in self.items:
            end = row.off_rent_date or row.charge_upto or self.expected_end_date
            if end and row.charge_from:
                units = get_billable_units(row.charge_from, end, row.rate_basis,
                                           row.min_billable_units)
                row.estimated_amount = line_amount(units, row.qty, row.rate,
                                                   row.discount_percent)
            else:
                row.estimated_amount = 0
            total += flt(row.estimated_amount)

        self.estimated_rental_amount = flt(total, 2)
        self.total_charges = flt(sum(flt(c.amount) for c in self.charges), 2)
        self.estimated_total = flt(self.estimated_rental_amount + self.total_charges, 2)

    def set_status(self, update=False):
        if self.docstatus == 0:
            status = "Draft"
        elif self.docstatus == 2:
            status = "Cancelled"
        elif self.status == "Closed":
            status = "Closed"
        else:
            today = getdate(nowdate())
            if getdate(self.start_date) > today:
                status = "Scheduled"
            elif (not self.is_open_ended and self.expected_end_date
                    and getdate(self.expected_end_date) < today):
                status = "Overdue"
            else:
                status = "Active"
        if update:
            self.db_set("status", status)
        else:
            self.status = status

    def on_submit(self):
        self.set_status(update=True)
        self.db_set("next_billing_date", self.start_date)
        for row in self.items:
            self.reserve_equipment(row)
        if self.reservation:
            frappe.db.set_value("Rental Reservation", self.reservation,
                                {"status": "Converted", "rental_contract": self.name})

    def reserve_equipment(self, row):
        equipment = frappe.get_doc("Rental Equipment", row.equipment)
        if equipment.status in ("Available", "Reserved"):
            equipment.set_status("Reserved", contract=self.name)

    def on_cancel(self):
        submitted = [i.sales_invoice for i in self.invoices
                     if i.sales_invoice and frappe.db.get_value(
                         "Sales Invoice", i.sales_invoice, "docstatus") == 1]
        if submitted:
            frappe.throw(_("Cancel the linked invoices first: {0}").format(
                ", ".join(submitted)))
        self.release_equipment()
        self.set_status(update=True)

    def release_equipment(self):
        for row in self.items:
            if frappe.db.get_value("Rental Equipment", row.equipment,
                                   "current_contract") == self.name:
                equipment = frappe.get_doc("Rental Equipment", row.equipment)
                equipment.set_status("Available", contract=None)

    @frappe.whitelist()
    def close_contract(self, close_date=None):
        close_date = getdate(close_date or nowdate())
        open_items = [r.equipment for r in self.items
                      if r.item_status == "On Rent"]
        if open_items:
            frappe.throw(_("These items are still on rent: {0}").format(
                ", ".join(open_items)))
        self.db_set("actual_end_date", close_date)
        self.db_set("status", "Closed")
        self.release_equipment()
        frappe.msgprint(_("Contract closed"), alert=True)

    @frappe.whitelist()
    def extend_contract(self, new_end_date):
        new_end_date = getdate(new_end_date)
        if new_end_date <= getdate(self.expected_end_date or self.start_date):
            frappe.throw(_("The new end date must be later than the current one"))
        for row in self.items:
            if row.item_status in ("Pending Dispatch", "On Rent"):
                validate_availability(row.equipment,
                                      add_days(self.expected_end_date, 1),
                                      new_end_date, ignore_contract=self.name)
                row.db_set("charge_upto", new_end_date, update_modified=False)
        self.db_set("expected_end_date", new_end_date)
        self.set_status(update=True)
        frappe.msgprint(_("Contract extended to {0}").format(new_end_date), alert=True)

    @frappe.whitelist()
    def bill_now(self, period_from=None, period_to=None):
        from equip_rental.utils.billing import create_invoice_for_contract
        period_from = period_from or self.next_billing_date or self.start_date
        period_to = period_to or nowdate()
        return create_invoice_for_contract(self.name, period_from, period_to)


@frappe.whitelist()
def make_dispatch_note(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.company = source.company

    def item_condition(row):
        return row.item_status == "Pending Dispatch"

    return get_mapped_doc("Rental Contract", source_name, {
        "Rental Contract": {
            "doctype": "Rental Dispatch Note",
            "field_map": {"name": "rental_contract", "site_address": "delivery_address"},
            "validation": {"docstatus": ["=", 1]},
        },
        "Rental Contract Item": {
            "doctype": "Rental Dispatch Item",
            "field_map": {"equipment": "equipment", "equipment_name": "equipment_name"},
            "condition": item_condition,
        },
    }, target_doc, post_process)


@frappe.whitelist()
def make_return_note(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.company = source.company

    def item_condition(row):
        return row.item_status == "On Rent"

    return get_mapped_doc("Rental Contract", source_name, {
        "Rental Contract": {
            "doctype": "Rental Return Note",
            "field_map": {"name": "rental_contract"},
            "validation": {"docstatus": ["=", 1]},
        },
        "Rental Contract Item": {
            "doctype": "Rental Return Item",
            "field_map": {"equipment": "equipment", "equipment_name": "equipment_name"},
            "condition": item_condition,
        },
    }, target_doc, post_process)
