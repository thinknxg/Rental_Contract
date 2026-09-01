import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class CrossHireRateAgreement(Document):
    def validate(self):
        if self.valid_upto and self.valid_from and getdate(self.valid_upto) < getdate(
                self.valid_from):
            frappe.throw(_("Valid Upto cannot be before Valid From"))


@frappe.whitelist()
def get_agreed_rate(supplier, equipment_category, rate_basis, date=None):
    """Rate lookup used when building a Cross Hire Order."""
    from frappe.utils import nowdate
    date = date or nowdate()

    agreements = frappe.get_all(
        "Cross Hire Rate Agreement",
        filters={"supplier": supplier, "is_active": 1},
        fields=["name", "valid_from", "valid_upto", "off_hire_notice_days"],
        order_by="valid_from desc")

    for agreement in agreements:
        if agreement.valid_from and getdate(date) < getdate(agreement.valid_from):
            continue
        if agreement.valid_upto and getdate(date) > getdate(agreement.valid_upto):
            continue
        for row in frappe.get_all(
                "Cross Hire Rate Agreement Item",
                filters={"parent": agreement.name, "rate_basis": rate_basis,
                         "equipment_category": equipment_category},
                fields=["rate", "min_hire_units", "transport_in", "transport_out"],
                limit=1):
            row["rate_agreement"] = agreement.name
            row["off_hire_notice_days"] = agreement.off_hire_notice_days
            return row
    return {}
