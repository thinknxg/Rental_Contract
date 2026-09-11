import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_dispatch_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.customer
        # rental_contract is intentionally left unset here — per the TL's
        # direction, going through a Rental Contract first is optional.
        # Dispatch Note can be created directly from Sales Order.

        target.items = []
        for so_item in source.items:
            equipment_list = frappe.get_all(
                "Rental Equipment",
                filters={"item": so_item.item_code, "status": "Available"},
                fields=["name", "current_location"],
                limit=int(so_item.qty),
            )

            if len(equipment_list) < so_item.qty:
                frappe.msgprint(
                    f"Only {len(equipment_list)} of {int(so_item.qty)} requested units "
                    f"available for item '{so_item.item_code}'. Add remaining rows manually.",
                    indicator="orange",
                    title="Partial Equipment Match",
                )

            for eq in equipment_list:
                target.append("items", {
                    "equipment": eq.name,
                    "warehouse": eq.current_location,
                })

    target_doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Rental Dispatch Note",
                "field_map": {"name": "sales_order"},
                "validation": {"docstatus": ["=", 1]},
            },
        },
        target_doc,
        set_missing_values,
    )
    return target_doc
