import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from equip_rental.utils.billing import create_invoice_for_contract


class RentalBillingRun(Document):
    def validate(self):
        if getdate(self.period_to) < getdate(self.period_from):
            frappe.throw(_("Period To cannot be before Period From"))

    def get_contracts(self):
        filters = {"docstatus": 1, "company": self.company,
                   "status": ["in", ["Active", "Overdue", "Scheduled"]],
                   "start_date": ["<=", self.period_to]}
        if self.contract_type and self.contract_type != "All":
            filters["contract_type"] = self.contract_type
        if self.billing_cycle and self.billing_cycle != "All":
            filters["billing_cycle"] = self.billing_cycle
        if self.customer:
            filters["customer"] = self.customer
        return frappe.get_all("Rental Contract", filters=filters, pluck="name")

    @frappe.whitelist()
    def execute(self):
        self.set("log", [])
        created = 0
        total = 0.0
        errors = 0

        for name in self.get_contracts():
            try:
                reference = create_invoice_for_contract(
                    name, self.period_from, self.period_to, submit=self.submit_invoices)
                if not reference:
                    self.append("log", {"rental_contract": name, "result": "Skipped",
                                        "remarks": _("Nothing billable in this period")})
                    continue
                doctype = ("Sales Invoice"
                           if frappe.db.exists("Sales Invoice", reference)
                           else "Journal Entry")
                amount = flt(frappe.db.get_value(
                    doctype, reference,
                    "grand_total" if doctype == "Sales Invoice" else "total_debit"))
                self.append("log", {
                    "rental_contract": name, "reference": reference,
                    "amount": amount,
                    "result": "Invoiced" if doctype == "Sales Invoice" else "Recharged"})
                created += 1
                total += amount
            except Exception:
                errors += 1
                frappe.log_error(frappe.get_traceback(),
                                 "Billing run {0} / {1}".format(self.name, name))
                self.append("log", {"rental_contract": name, "result": "Failed",
                                    "remarks": _("See the Error Log")})

        self.invoices_created = created
        self.total_amount = flt(total, 2)
        self.status = "Completed with Errors" if errors else "Completed"
        self.save()
        return {"created": created, "total": self.total_amount, "errors": errors}
