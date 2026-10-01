import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_dispatch_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.rental_contract = source.name
        target.customer = source.customer
        target.company = source.company

        target.items = []
        for so_item in source.items:
            pending = flt_qty = (so_item.qty or 0) - (so_item.delivered_qty or 0)
            if pending <= 0:
                continue
            target.append("items", {
                "item_code": so_item.item_code,
                "item_name": so_item.item_name,
                "qty": pending,
                "rate": so_item.rate,
                "amount": pending * (so_item.rate or 0),
                "warehouse": so_item.get("warehouse"),
                "sales_order": source.name,
                "sales_order_item": so_item.name,
            })

    from frappe.utils import flt

    target_doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Rental Dispatch Note",
                "validation": {"docstatus": ["=", 1]},
            },
        },
        target_doc,
        set_missing_values,
    )
    return target_doc
