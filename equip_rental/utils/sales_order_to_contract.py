import frappe
from frappe.model.mapper import get_mapped_doc


@frappe.whitelist()
def make_rental_contract(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.customer = source.customer
        target.contract_type = "Customer Rental"
        target.contract_date = frappe.utils.today()
        target.start_date = frappe.utils.today()
        target.company = source.company
        target.currency = source.currency

        target.items = []
        for so_item in source.items:
            equipment_list = frappe.get_all(
                "Rental Equipment",
                filters={"item": so_item.item_code, "status": "Available"},
                fields=["name", "equipment_name", "equipment_category"],
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
                    "equipment_name": eq.equipment_name,
                    "equipment_category": eq.equipment_category,
                    "item": so_item.item_code,
                    "qty": 1,
                    "rate": so_item.rate,
                })

    target_doc = get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Rental Contract",
                "field_map": {"name": "sales_order"},
                "validation": {"docstatus": ["=", 1]},
            },
        },
        target_doc,
        set_missing_values,
    )
    return target_doc
