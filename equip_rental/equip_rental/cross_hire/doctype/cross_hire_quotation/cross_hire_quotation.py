import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt


class CrossHireQuotation(Document):
    def validate(self):
        total = 0.0
        for row in self.items:
            total += flt(row.rate) * (flt(row.qty) or 1)
            total += flt(row.transport_in) + flt(row.transport_out)
        self.total_amount = flt(total, 2)


@frappe.whitelist()
def compare(cross_hire_requisition):
    """Side by side vendor comparison for one requisition."""
    rows = frappe.db.sql("""
        select q.name as quotation, q.supplier, q.valid_upto, q.lead_time_days,
            i.equipment_category, i.description, i.rate_basis, i.rate, i.qty,
            i.transport_in, i.transport_out, i.min_hire_units
        from `tabCross Hire Quotation Item` i
        inner join `tabCross Hire Quotation` q on q.name = i.parent
        where q.cross_hire_requisition = %s and q.status != 'Rejected'
        order by i.equipment_category asc, i.rate asc
    """, cross_hire_requisition, as_dict=True)
    return rows


@frappe.whitelist()
def make_cross_hire_order(source_name, target_doc=None):
    def post_process(source, target):
        target.hire_purpose = "Re-Hire to Customer"
        target.vendor_reference = source.vendor_reference
        requisition = source.cross_hire_requisition
        if requisition:
            details = frappe.db.get_value(
                "Cross Hire Requisition", requisition,
                ["required_from", "required_upto", "customer", "project", "cost_center",
                 "rental_contract", "purpose"], as_dict=True)
            target.from_date = details.required_from
            target.expected_to_date = details.required_upto
            target.customer = details.customer
            target.project = details.project
            target.cost_center = details.cost_center
            target.rental_contract = details.rental_contract
            target.hire_purpose = details.purpose
        target.run_method("set_missing_values")

    def item_condition(row):
        return bool(row.is_selected)

    def update_item(source_row, target_row, source_parent):
        target_row.expected_from_date = frappe.db.get_value(
            "Cross Hire Requisition", source_parent.cross_hire_requisition,
            "required_from")
        target_row.expected_off_hire_date = frappe.db.get_value(
            "Cross Hire Requisition", source_parent.cross_hire_requisition,
            "required_upto")
        target_row.cross_hire_requisition = source_parent.cross_hire_requisition

    return get_mapped_doc("Cross Hire Quotation", source_name, {
        "Cross Hire Quotation": {
            "doctype": "Cross Hire Order",
            "field_map": {"supplier": "supplier", "currency": "currency",
                          "company": "company"},
        },
        "Cross Hire Quotation Item": {
            "doctype": "Cross Hire Order Item",
            "field_map": {"equipment_category": "equipment_category",
                          "description": "description", "qty": "qty",
                          "rate_basis": "rate_basis", "rate": "rate",
                          "min_hire_units": "min_hire_units",
                          "transport_in": "transport_in",
                          "transport_out": "transport_out",
                          "vendor_plant_no": "vendor_plant_no"},
            "condition": item_condition,
            "postprocess": update_item,
        },
    }, target_doc, post_process)
