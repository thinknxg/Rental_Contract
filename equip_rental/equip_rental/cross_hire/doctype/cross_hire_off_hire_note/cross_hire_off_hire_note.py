import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, flt, getdate

from equip_rental.utils.common import get_settings


class CrossHireOffHireNote(Document):
    def validate(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        self.company = self.company or order.company

        if getdate(self.requested_collection_date) < getdate(self.notice_date):
            frappe.throw(_("The collection date cannot be before the notice date"))

        self.check_notice_period(order)
        self.check_still_on_customer_contract()
        self.check_vendor_reference()

        self.total_damage_charged = flt(
            sum(flt(row.damage_charged) for row in self.items), 2)

    def check_notice_period(self, order):
        notice_days = int(order.off_hire_notice_days or 0)
        if not notice_days:
            return
        given = date_diff(self.requested_collection_date, self.notice_date)
        if given < notice_days:
            frappe.msgprint(
                _("{0} requires {1} days notice but only {2} has been given. "
                  "They may keep charging until {3}.").format(
                    order.supplier, notice_days, given,
                    add_days(self.notice_date, notice_days)),
                title=_("Short Notice"), indicator="orange")

    def check_still_on_customer_contract(self):
        """Never off-hire to the vendor while a customer still has the machine."""
        for row in self.items:
            if not row.rental_equipment:
                continue
            live = frappe.db.sql("""
                select c.name from `tabRental Contract Item` ci
                inner join `tabRental Contract` c on c.name = ci.parent
                where ci.equipment = %s and c.docstatus = 1
                    and ci.item_status = 'On Rent' limit 1""", row.rental_equipment)
            if live:
                frappe.throw(
                    _("Row {0}: {1} is still on rent to a customer under {2}. "
                      "Take the return from the customer first.").format(
                        row.idx, row.rental_equipment, live[0][0]))

    def check_vendor_reference(self):
        settings = get_settings()
        if (settings.require_vendor_offhire_reference and self.actual_off_hire_date
                and not self.vendor_off_hire_reference):
            frappe.throw(
                _("Record the vendor's off-hire reference. Without it you cannot "
                  "prove when their charges stopped."))

    def on_submit(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        collected = bool(self.actual_off_hire_date)

        for row in self.items:
            item = self.get_order_item(order, row)
            if not item:
                continue
            item.db_set("off_hire_notice_date", getdate(self.notice_date),
                        update_modified=False)
            item.db_set("vendor_off_hire_reference", self.vendor_off_hire_reference,
                        update_modified=False)
            item.db_set("damage_charged",
                        flt(item.damage_charged) + flt(row.damage_charged),
                        update_modified=False)

            if collected:
                item.db_set("actual_off_hire_date", getdate(self.actual_off_hire_date),
                            update_modified=False)
                item.db_set("meter_out", flt(row.meter_out), update_modified=False)
                item.db_set("item_status", "Off Hired", update_modified=False)
                self.release_equipment(row, item)
            else:
                item.db_set("item_status", "Off-Hire Requested", update_modified=False)
                if item.rental_equipment:
                    frappe.db.set_value(
                        "Rental Equipment", item.rental_equipment,
                        "hire_available_upto", getdate(self.requested_collection_date),
                        update_modified=False)

            if flt(row.damage_charged):
                self.raise_damage_claim(order, row, item)

        order.reload()
        status = order.set_status_from_items()
        if self.close_order and status == "Off Hired":
            order.db_set("status", "Closed")

    def release_equipment(self, row, item):
        """The unit goes back to the vendor - it must leave the available fleet."""
        if not item.rental_equipment:
            return
        frappe.db.set_value("Rental Equipment", item.rental_equipment, {
            "status": "Retired",
            "hire_available_upto": getdate(self.actual_off_hire_date),
            "current_contract": None,
        }, update_modified=False)

    def raise_damage_claim(self, order, row, item):
        claim = frappe.new_doc("Cross Hire Damage Claim")
        claim.cross_hire_order = order.name
        claim.rental_equipment = row.rental_equipment
        claim.company = self.company
        claim.claim_date = self.actual_off_hire_date or self.notice_date
        claim.claimed_amount = flt(row.damage_charged)
        claim.recoverable_from_customer = row.recoverable_from_customer
        claim.rental_contract = row.rental_contract
        claim.damage_description = row.damage_notes
        claim.flags.ignore_permissions = True
        claim.insert()

    def get_order_item(self, order, row):
        for item in order.items:
            if row.order_row and item.name == row.order_row:
                return item
            if row.rental_equipment and item.rental_equipment == row.rental_equipment:
                return item
        return None

    def on_cancel(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        for row in self.items:
            item = self.get_order_item(order, row)
            if not item:
                continue
            item.db_set("item_status", "On Hire", update_modified=False)
            item.db_set("actual_off_hire_date", None, update_modified=False)
            if item.rental_equipment:
                frappe.db.set_value("Rental Equipment", item.rental_equipment,
                                    "status", "Available", update_modified=False)
        order.reload()
        order.set_status_from_items()
