import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class CrossHireDamageClaim(Document):
    def validate(self):
        if self.status in ("Accepted", "Recovered") and not self.accepted_amount:
            self.accepted_amount = flt(self.claimed_amount)
        self.net_cost = flt(flt(self.accepted_amount) - flt(self.recovered_amount), 2)
        if self.recoverable_from_customer and not self.rental_contract:
            frappe.throw(_("Select the customer contract the damage is recoverable from"))

    @frappe.whitelist()
    def recover_from_customer(self, amount=None):
        """Push the vendor's damage charge onto the customer contract so it is
        billed on the next invoice."""
        if not self.rental_contract:
            frappe.throw(_("No customer contract linked"))
        amount = flt(amount or self.accepted_amount or self.claimed_amount)
        if not amount:
            frappe.throw(_("Nothing to recover"))

        contract = frappe.get_doc("Rental Contract", self.rental_contract)
        charge_type = "Damage Recovery"
        if not frappe.db.exists("Rental Charge Type", charge_type):
            frappe.throw(_("Charge type {0} is missing").format(charge_type))

        charge = contract.append("charges", {})
        charge.charge_type = charge_type
        charge.item = frappe.db.get_value("Rental Charge Type", charge_type, "item")
        charge.amount = amount
        charge.description = _("Cross hire damage {0} ({1})").format(
            self.name, self.rental_equipment or "")
        contract.flags.ignore_validate_update_after_submit = True
        contract.save(ignore_permissions=True)

        self.db_set("recovered_amount", flt(self.recovered_amount) + amount)
        self.db_set("net_cost", flt(self.accepted_amount) - flt(self.recovered_amount))
        self.db_set("status", "Recovered")
        frappe.msgprint(_("Added {0} to contract {1}").format(amount,
                                                              self.rental_contract),
                        alert=True)
