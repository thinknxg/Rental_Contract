import frappe
from frappe.utils import flt


def _get_item_flags(item_code):
    return frappe.db.get_value(
        "Item", item_code, ["is_rental_item", "is_job_type_item"], as_dict=True
    )


def _explode_line(item_code, qty):
    """Returns a list of (component_item_code, qty) pairs. Job Type items
    explode via their own Item Names table on the Item itself; plain
    rental items are a single line."""
    flags = _get_item_flags(item_code)
    if flags and flags.is_job_type_item:
        item = frappe.get_doc("Item", item_code)
        components = item.get("job_type_item_names")
        if not components:
            frappe.throw(f"No component items defined for Job Type item {item_code}")
        return [(row.item_code, flt(row.quantity) * flt(qty)) for row in components]
    return [(item_code, flt(qty))]


def issue_stock_on_hire_order_submit(doc, method=None):
    """Hire Order / Hire Order Contract on_submit: rental and job type
    items leave the warehouse -- job type items explode into their
    Product Bundle components."""
    settings = frappe.get_single("Equipment Rental Settings")
    warehouse = settings.default_warehouse
    if not warehouse:
        frappe.throw("Set a Default Equipment Warehouse in Equipment Rental Settings first")

    lines = []
    for row in doc.items:
        if not row.item_code:
            continue
        lines.extend(_explode_line(row.item_code, row.qty))

    if not lines:
        return

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Issue"
    se.company = settings.default_company or doc.get("company")
    for item_code, qty in lines:
        se.append("items", {
            "item_code": item_code, "qty": qty, "s_warehouse": warehouse,
            "allow_zero_valuation_rate": 1,
        })
    se.insert(ignore_permissions=True)
    se.submit()

    frappe.db.set_value(doc.doctype, doc.name, "custom_stock_issue_entry", se.name)


def receive_stock_on_hire_return_submit(doc, method=None):
    """Hire Return Note on_submit: good qty returns to the default
    warehouse, damage qty is received into the damage/scrap warehouse --
    job type items explode into Product Bundle components first."""
    settings = frappe.get_single("Equipment Rental Settings")
    good_warehouse = settings.default_warehouse
    damage_warehouse = settings.damage_warehouse

    if not good_warehouse:
        frappe.throw("Set a Default Equipment Warehouse in Equipment Rental Settings first")

    lines = []
    for row in doc.items:
        if not row.item_code:
            continue
        if flt(row.good_qty):
            for item_code, qty in _explode_line(row.item_code, row.good_qty):
                lines.append((item_code, qty, good_warehouse))
        if flt(row.damage_qty):
            if not damage_warehouse:
                frappe.throw("Set a Damage/Scrap Warehouse in Equipment Rental Settings first")
            for item_code, qty in _explode_line(row.item_code, row.damage_qty):
                lines.append((item_code, qty, damage_warehouse))

    if not lines:
        return

    se = frappe.new_doc("Stock Entry")
    se.stock_entry_type = "Material Receipt"
    se.company = settings.default_company
    for item_code, qty, t_warehouse in lines:
        se.append("items", {
            "item_code": item_code, "qty": qty, "t_warehouse": t_warehouse,
            "allow_zero_valuation_rate": 1,
        })
    se.insert(ignore_permissions=True)
    se.submit()

    frappe.db.set_value(doc.doctype, doc.name, "custom_stock_receipt_entry", se.name)
