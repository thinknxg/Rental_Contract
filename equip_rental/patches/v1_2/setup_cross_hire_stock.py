"""Provision the stock and procurement masters the cross hire cycle needs.

Hired-in equipment is received into its own warehouse at zero valuation, so it
never mingles with owned stock and never touches the General Ledger.
"""

import frappe
from frappe.utils import cint


def execute():
    frappe.reload_doc("equipment_rental", "doctype", "equipment_rental_settings")
    frappe.reload_doc("equipment_rental", "doctype", "equipment_category")
    frappe.reload_doc("equipment_rental", "doctype", "rental_equipment")
    frappe.reload_doc("cross_hire", "doctype", "cross_hire_order_item")

    settings = frappe.get_single("Equipment Rental Settings")
    company = settings.default_company or frappe.defaults.get_defaults().get("company")
    if not company:
        return

    abbr = frappe.db.get_value("Company", company, "abbr")

    if not settings.cross_hire_item_group:
        settings.cross_hire_item_group = _ensure_item_group("Cross Hire Equipment")
    if not settings.cross_hire_warehouse:
        settings.cross_hire_warehouse = _ensure_warehouse("Cross Hire Yard", company,
                                                          abbr)
    if not settings.cross_hire_site_warehouse:
        settings.cross_hire_site_warehouse = _ensure_warehouse(
            "Cross Hire On Site", company, abbr)
    if not settings.cross_hire_item:
        settings.cross_hire_item = _ensure_hire_charge_item(settings)

    settings.flags.ignore_mandatory = True
    settings.save(ignore_permissions=True)

    _backfill_stock_items()
    frappe.db.commit()


def _ensure_item_group(name):
    if frappe.db.exists("Item Group", name):
        return name
    parent = frappe.db.get_value("Item Group", {"is_group": 1, "parent_item_group": ""},
                                 "name") or "All Item Groups"
    group = frappe.new_doc("Item Group")
    group.item_group_name = name
    group.parent_item_group = parent
    group.is_group = 0
    group.flags.ignore_permissions = True
    group.insert()
    return group.name


def _ensure_warehouse(name, company, abbr):
    full_name = "{0} - {1}".format(name, abbr) if abbr else name
    if frappe.db.exists("Warehouse", full_name):
        return full_name
    parent = frappe.db.get_value("Warehouse",
                                 {"company": company, "is_group": 1}, "name")
    warehouse = frappe.new_doc("Warehouse")
    warehouse.warehouse_name = name
    warehouse.company = company
    warehouse.parent_warehouse = parent
    warehouse.flags.ignore_permissions = True
    warehouse.insert()
    return warehouse.name


def _ensure_hire_charge_item(settings):
    item_code = "CROSS-HIRE-CHARGES"
    if frappe.db.exists("Item", item_code):
        return item_code
    item = frappe.new_doc("Item")
    item.item_code = item_code
    item.item_name = "Cross hire charges"
    item.item_group = (settings.rental_item_group or settings.cross_hire_item_group
                       or "All Item Groups")
    item.stock_uom = "Nos"
    item.is_stock_item = 0
    item.is_purchase_item = 1
    item.is_sales_item = 0
    item.is_rental_item = 1
    item.description = ("Periodic hire charges invoiced by the vendor for "
                        "equipment hired in. Non-stock service item.")
    item.flags.ignore_permissions = True
    item.insert()
    return item.name


def _backfill_stock_items():
    """Give every category used by an existing cross hire order its stock item."""
    from equip_rental.utils.cross_hire_stock import ensure_stock_item

    categories = frappe.db.sql_list("""
        select distinct i.equipment_category
        from `tabCross Hire Order Item` i
        where ifnull(i.equipment_category, '') != ''""")

    for category in categories:
        if not frappe.db.exists("Equipment Category", category):
            continue
        try:
            item_code = ensure_stock_item(category)
            frappe.db.sql("""update `tabCross Hire Order Item`
                set item_code = %s
                where equipment_category = %s and ifnull(item_code, '') = ''""",
                (item_code, category))
        except Exception:
            frappe.log_error(frappe.get_traceback(),
                             "Cross hire stock item backfill: {0}".format(category))

    if cint(frappe.db.count("Rental Equipment", {"ownership": "Cross-Hired"})):
        frappe.db.sql("""
            update `tabRental Equipment` e
            inner join `tabCross Hire Order Item` i on i.rental_equipment = e.name
            set e.stock_item = i.item_code
            where ifnull(e.stock_item, '') = '' and ifnull(i.item_code, '') != ''""")
