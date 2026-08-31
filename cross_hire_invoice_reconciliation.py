import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from equip_rental.utils.common import get_settings
from equip_rental.utils.cross_hire import expected_cost


class CrossHireInvoiceReconciliation(Document):
    def validate(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        self.company = self.company or order.company
        if getdate(self.period_to) < getdate(self.period_from):
            frappe.throw(_("Period To cannot be before Period From"))

        expected = claimed = variance = approved = 0.0
        for row in self.items:
            row.variance = flt(flt(row.claimed_amount) - flt(row.expected_amount), 2)
            if row.decision == "Accept":
                row.approved_amount = flt(row.claimed_amount)
            elif row.decision == "Accept Expected":
                row.approved_amount = flt(row.expected_amount)
            else:
                row.approved_amount = 0
            if row.variance and not row.variance_reason and row.decision == "Accept":
                frappe.msgprint(
                    _("Row {0}: accepting a variance of {1} without a reason").format(
                        row.idx, row.variance), indicator="orange", alert=True)
            expected += flt(row.expected_amount)
            claimed += flt(row.claimed_amount)
            variance += flt(row.variance)
            approved += flt(row.approved_amount)

        self.total_expected = flt(expected, 2)
        self.total_claimed = flt(claimed, 2)
        self.total_variance = flt(variance, 2)
        self.total_approved = flt(approved, 2)

        if self.docstatus == 0:
            if any(r.decision == "Dispute" for r in self.items):
                self.status = "Disputed"
            elif abs(self.total_variance) > 0.01:
                self.status = "Variance"
            elif self.items:
                self.status = "Matched"

    @frappe.whitelist()
    def pull_expected(self):
        """Rebuild the expected side from the hire itself - the vendor's claim is
        then compared line by line against what we actually held."""
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        self.set("items", [])

        for item in order.items:
            if item.item_status == "Cancelled":
                continue
            since = item.invoiced_upto and frappe.utils.add_days(item.invoiced_upto, 1)
            start = max(getdate(since or self.period_from), getdate(self.period_from))
            units, amount = expected_cost(item, order, upto=self.period_to, since=start)
            if not units:
                continue
            row = self.append("items", {})
            row.order_row = item.name
            row.description = item.description or item.equipment_category
            row.charge_from = start
            row.charge_upto = min(
                getdate(self.period_to),
                getdate(item.actual_off_hire_date) if item.actual_off_hire_date
                else getdate(self.period_to))
            row.expected_units = units
            row.expected_amount = amount
            row.claimed_units = units
            row.claimed_amount = amount
            row.decision = "Accept"

        self.save()
        return len(self.items)

    def on_submit(self):
        if self.status == "Disputed":
            frappe.msgprint(_("Disputed lines are excluded from the purchase invoice"),
                            indicator="orange")
        invoice = self.make_purchase_invoice()
        self.db_set("purchase_invoice", invoice)
        self.db_set("status", "Invoiced")
        self.update_order()

    def make_purchase_invoice(self):
        settings = get_settings()
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        item_code = settings.cross_hire_item
        if not item_code:
            frappe.throw(_("Set a Cross Hire Item in Equipment Rental Settings"))

        payable_lines = [r for r in self.items if flt(r.approved_amount)]
        if not payable_lines:
            return None

        invoice = frappe.new_doc("Purchase Invoice")
        invoice.supplier = order.supplier
        invoice.company = self.company
        invoice.currency = order.currency
        invoice.bill_no = self.vendor_invoice_no
        invoice.bill_date = self.vendor_invoice_date
        invoice.cross_hire_order = order.name
        invoice.cross_hire_reconciliation = self.name
        invoice.project = order.project
        invoice.cost_center = order.cost_center

        for row in payable_lines:
            line = invoice.append("items", {})
            line.item_code = item_code
            line.qty = 1
            line.rate = flt(row.approved_amount)
            line.cost_center = order.cost_center
            line.project = order.project
            if settings.default_cross_hire_expense_account:
                line.expense_account = settings.default_cross_hire_expense_account
            line.description = _("Cross hire {0}: {1} {2} to {3}").format(
                order.name, row.description, row.charge_from, row.charge_upto)

        invoice.set_missing_values()
        invoice.flags.ignore_permissions = True
        invoice.insert()
        return invoice.name

    def update_order(self):
        order = frappe.get_doc("Cross Hire Order", self.cross_hire_order)
        total = 0.0
        for row in self.items:
            for item in order.items:
                if item.name != row.order_row:
                    continue
                item.db_set("invoiced_upto", getdate(row.charge_upto),
                            update_modified=False)
                item.db_set("invoiced_amount",
                            flt(item.invoiced_amount) + flt(row.approved_amount),
                            update_modified=False)
            total += flt(row.approved_amount)
        order.db_set("invoiced_cost", flt(order.invoiced_cost) + flt(total, 2))

    def on_cancel(self):
        if self.purchase_invoice and frappe.db.get_value(
                "Purchase Invoice", self.purchase_invoice, "docstatus") == 1:
            frappe.throw(_("Cancel the purchase invoice {0} first").format(
                self.purchase_invoice))
        self.db_set("status", "Draft")
