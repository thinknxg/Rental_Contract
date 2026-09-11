import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_return_note_from_dispatch(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.customer
        target.rental_contract = source.rental_contract

        # Aggregate dispatch rows by item_code (via Rental Equipment.item)
        aggregated = {}
        for d_item in source.items:
            equipment = frappe.get_doc("Rental Equipment", d_item.equipment)
            item_code = equipment.item
            key = item_code

            if key not in aggregated:
                aggregated[key] = {
                    "item_code": item_code,
                    "item_name": equipment.equipment_name,
                    "warehouse": d_item.warehouse,
                    "qty_to_return": 0,
                    "project": d_item.project,
                    "rental_contract": d_item.rental_contract,
                }
            aggregated[key]["qty_to_return"] += 1

        target.items = []
        for row in aggregated.values():
            target.append("items", row)

    target_doc = get_mapped_doc(
        "Rental Dispatch Note",
        source_name,
        {
            "Rental Dispatch Note": {
                "doctype": "Rental Return Note",
                "field_map": {"name": "rental_dispatch_note"},
                "validation": {"docstatus": ["=", 1]},
            },
        },
        target_doc,
        set_missing_values,
    )
    return target_doc
