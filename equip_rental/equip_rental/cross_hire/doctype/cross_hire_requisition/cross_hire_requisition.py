import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import getdate


class CrossHireRequisition(Document):
    def validate(self):
        if self.required_upto and getdate(self.required_upto) < getdate(
                self.required_from):
            frappe.throw(_("Required Upto cannot be before Required From"))
        for row in self.items:
            if not row.required_from:
                row.required_from = self.required_from
            if not row.required_upto:
                row.required_upto = self.required_upto
        self.set_status()

    def set_status(self):
        if self.status == "Cancelled":
            return
        ordered = [r for r in self.items if r.item_status == "Ordered"]
        if not ordered:
            self.status = "Open" if self.status != "Draft" else self.status
        elif len(ordered) == len(self.items):
            self.status = "Ordered"
        else:
            self.status = "Partially Ordered"

    @frappe.whitelist()
    def check_own_fleet(self):
        """Before hiring in, show what we already own for these categories."""
        from equip_rental.utils.availability import get_available_equipment
        result = []
        for row in self.items:
            available = get_available_equipment(
                self.required_from, self.required_upto or self.required_from,
                equipment_category=row.equipment_category, company=self.company)
            owned = [a for a in available
                     if frappe.db.get_value("Rental Equipment", a["name"],
                                            "ownership") == "Owned"]
            result.append({"row": row.idx, "category": row.equipment_category,
                           "own_fleet_available": len(owned),
                           "equipment": [a["name"] for a in owned][:10]})
        return result


@frappe.whitelist()
def make_cross_hire_order(source_name, target_doc=None):
    def post_process(source, target):
        target.from_date = source.required_from
        target.expected_to_date = source.required_upto
        target.hire_purpose = source.purpose
        target.run_method("set_missing_values")

    def update_item(source_row, target_row, source_parent):
        target_row.expected_from_date = source_row.required_from \
            or source_parent.required_from
        target_row.expected_off_hire_date = source_row.required_upto \
            or source_parent.required_upto
        target_row.rate = source_row.target_rate
        target_row.cross_hire_requisition = source_parent.name

    return get_mapped_doc("Cross Hire Requisition", source_name, {
        "Cross Hire Requisition": {
            "doctype": "Cross Hire Order",
            "field_map": {"customer": "customer", "project": "project",
                          "cost_center": "cost_center",
                          "rental_contract": "rental_contract"},
        },
        "Cross Hire Requisition Item": {
            "doctype": "Cross Hire Order Item",
            "field_map": {"equipment_category": "equipment_category",
                          "description": "description", "qty": "qty",
                          "rate_basis": "rate_basis"},
            "postprocess": update_item,
        },
    }, target_doc, post_process)
