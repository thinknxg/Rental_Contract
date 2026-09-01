import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, nowdate

from equip_rental.utils.common import get_settings
from equip_rental.utils.cross_hire import expected_cost
from equip_rental.utils.pricing import get_billable_units


class CrossHireOrder(Document):
    def validate(self):
        self.set_missing_values()
        self.validate_dates()
        self.validate_back_to_back()
        self.calculate_totals()

    def set_missing_values(self):
        settings = get_settings()
        if not self.company:
            self.company = settings.default_company
        if not self.currency:
            self.currency = frappe.db.get_value("Company", self.company,
                                                "default_currency")
        if not self.cost_center:
            self.cost_center = frappe.db.get_value("Company", self.company,
                                                   "cost_center")
        if not self.off_hire_notice_days:
            self.off_hire_notice_days = (
                frappe.db.get_value("Cross Hire Rate Agreement", self.rate_agreement,
                                    "off_hire_notice_days")
                or settings.default_off_hire_notice_days or 0)

        for row in self.items:
            if not row.expected_from_date:
                row.expected_from_date = self.from_date
            if not row.expected_off_hire_date and not self.is_open_ended:
                row.expected_off_hire_date = self.expected_to_date
            if not row.rate and self.rate_agreement:
                self.apply_agreement_rate(row)

    def apply_agreement_rate(self, row):
        agreed = frappe.get_all(
            "Cross Hire Rate Agreement Item",
            filters={"parent": self.rate_agreement, "rate_basis": row.rate_basis,
                     "equipment_category": row.equipment_category},
            fields=["rate", "min_hire_units", "transport_in", "transport_out"], limit=1)
        if agreed:
            row.rate = agreed[0].rate
            row.min_hire_units = row.min_hire_units or agreed[0].min_hire_units
            row.transport_in = row.transport_in or agreed[0].transport_in
            row.transport_out = row.transport_out or agreed[0].transport_out

    def validate_dates(self):
        if not self.is_open_ended and self.expected_to_date and getdate(
                self.expected_to_date) < getdate(self.from_date):
            frappe.throw(_("Expected Hire Upto cannot be before Hire From"))
        for row in self.items:
            if row.expected_off_hire_date and getdate(
                    row.expected_off_hire_date) < getdate(row.expected_from_date):
                frappe.throw(_("Row {0}: off-hire date is before the on-hire date")
                             .format(row.idx))

    def validate_back_to_back(self):
        """When the hire backs a customer contract, we must hold the equipment for
        at least as long as we promised it."""
        if not (self.back_to_back and self.rental_contract):
            return
        contract = frappe.db.get_value(
            "Rental Contract", self.rental_contract,
            ["start_date", "expected_end_date", "is_open_ended"], as_dict=True)
        if not contract:
            return
        if getdate(self.from_date) > getdate(contract.start_date):
            frappe.msgprint(
                _("This hire starts after the customer contract starts ({0}).").format(
                    contract.start_date), indicator="orange", alert=True)
        if (not self.is_open_ended and not contract.is_open_ended
                and contract.expected_end_date
                and getdate(self.expected_to_date or self.from_date)
                < getdate(contract.expected_end_date)):
            frappe.throw(
                _("The customer contract {0} runs to {1} but this hire ends on {2}. "
                  "Extend the hire or shorten the contract.").format(
                    self.rental_contract, contract.expected_end_date,
                    self.expected_to_date), title=_("Back-to-Back Gap"))

    def calculate_totals(self):
        hire = 0.0
        transport = 0.0
        for row in self.items:
            end = row.expected_off_hire_date or self.expected_to_date
            if end and row.expected_from_date:
                row.expected_units = get_billable_units(
                    row.expected_from_date, end, row.rate_basis, row.min_hire_units)
                row.expected_amount = flt(
                    flt(row.expected_units) * (flt(row.qty) or 1) * flt(row.rate), 2)
            else:
                row.expected_units = 0
                row.expected_amount = 0
            hire += flt(row.expected_amount)
            transport += flt(row.transport_in) + flt(row.transport_out)

        self.estimated_hire_cost = flt(hire, 2)
        self.transport_cost = flt(transport, 2)
        self.estimated_total_cost = flt(hire + transport, 2)

    def on_submit(self):
        self.db_set("status", "Ordered")
        for row in self.items:
            if row.cross_hire_requisition:
                frappe.db.sql("""update `tabCross Hire Requisition Item`
                    set item_status = 'Ordered', cross_hire_order = %s
                    where parent = %s and equipment_category = %s
                        and item_status != 'Ordered' limit 1""",
                    (self.name, row.cross_hire_requisition, row.equipment_category))

    def on_cancel(self):
        received = frappe.db.exists("Cross Hire Receipt",
                                    {"cross_hire_order": self.name, "docstatus": 1})
        if received:
            frappe.throw(_("Cancel the cross hire receipts first"))
        self.db_set("status", "Cancelled")

    def set_status_from_items(self):
        statuses = [row.item_status for row in self.items
                    if row.item_status != "Cancelled"]
        if not statuses:
            status = "Cancelled"
        elif all(s == "Off Hired" for s in statuses):
            status = "Off Hired"
        elif any(s == "Off Hired" for s in statuses):
            status = "Partially Off-Hired"
        elif any(s in ("On Hire", "Off-Hire Requested") for s in statuses):
            status = "On Hire"
        else:
            status = "Ordered"
        self.db_set("status", status)
        return status

    @frappe.whitelist()
    def extend_hire(self, new_off_hire_date, vendor_approval_reference=None, row=None):
        """Extend the vendor hire, then widen the window on the fleet records so the
        units can be committed to customers for the longer period."""
        new_off_hire_date = getdate(new_off_hire_date)
        changed = 0
        for item in self.items:
            if row and item.name != row:
                continue
            if item.item_status not in ("Ordered", "On Hire"):
                continue
            old = item.expected_off_hire_date
            if old and new_off_hire_date <= getdate(old):
                continue
            item.db_set("expected_off_hire_date", new_off_hire_date,
                        update_modified=False)
            if item.rental_equipment:
                frappe.db.set_value("Rental Equipment", item.rental_equipment,
                                    "hire_available_upto", new_off_hire_date,
                                    update_modified=False)
            self.append("amendments", {
                "amendment_date": nowdate(), "amendment_type": "Extension",
                "reference_row": item.description or item.name,
                "old_value": str(old or ""), "new_value": str(new_off_hire_date),
                "approved_by": vendor_approval_reference,
            })
            changed += 1

        if not changed:
            frappe.throw(_("Nothing to extend"))

        if not self.is_open_ended and (not self.expected_to_date
                                       or new_off_hire_date > getdate(
                                           self.expected_to_date)):
            self.db_set("expected_to_date", new_off_hire_date)

        self.flags.ignore_validate_update_after_submit = True
        self.save(ignore_permissions=True)
        frappe.msgprint(_("Hire extended to {0} on {1} line(s)").format(
            new_off_hire_date, changed), alert=True)

    @frappe.whitelist()
    def cost_to_date(self):
        rows = []
        for item in self.items:
            units, amount = expected_cost(item, self)
            rows.append({"description": item.description or item.name,
                         "units": units, "amount": amount,
                         "invoiced": flt(item.invoiced_amount),
                         "uninvoiced": flt(amount) - flt(item.invoiced_amount)})
        return rows


@frappe.whitelist()
def make_cross_hire_receipt(source_name, target_doc=None):
    def post_process(source, target):
        target.company = source.company

    def item_condition(row):
        return row.item_status == "Ordered"

    def update_item(source_row, target_row, source_parent):
        target_row.order_row = source_row.name

    return get_mapped_doc("Cross Hire Order", source_name, {
        "Cross Hire Order": {
            "doctype": "Cross Hire Receipt",
            "field_map": {"name": "cross_hire_order",
                          "delivery_address": "delivery_address"},
            "validation": {"docstatus": ["=", 1]},
        },
        "Cross Hire Order Item": {
            "doctype": "Cross Hire Receipt Item",
            "field_map": {"equipment_category": "equipment_category",
                          "description": "description",
                          "vendor_plant_no": "vendor_plant_no"},
            "condition": item_condition,
            "postprocess": update_item,
        },
    }, target_doc, post_process)


@frappe.whitelist()
def make_off_hire_note(source_name, target_doc=None):
    def post_process(source, target):
        target.company = source.company
        target.notice_date = nowdate()

    def item_condition(row):
        return row.item_status in ("On Hire", "Off-Hire Requested")

    def update_item(source_row, target_row, source_parent):
        target_row.order_row = source_row.name

    return get_mapped_doc("Cross Hire Order", source_name, {
        "Cross Hire Order": {
            "doctype": "Cross Hire Off Hire Note",
            "field_map": {"name": "cross_hire_order"},
            "validation": {"docstatus": ["=", 1]},
        },
        "Cross Hire Order Item": {
            "doctype": "Cross Hire Off Hire Item",
            "field_map": {"rental_equipment": "rental_equipment",
                          "description": "description"},
            "condition": item_condition,
            "postprocess": update_item,
        },
    }, target_doc, post_process)
