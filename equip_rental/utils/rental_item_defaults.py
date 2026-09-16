import frappe


def apply_rental_item_defaults(doc, method=None):
    """Item validate() hook: when Is Rental Item is ticked, auto-set the
    item's item_group, per-company income/expense accounts (Item Default),
    and the rental item tax template -- so rental items post to a separate
    income account and use rental-specific defaults automatically."""
    if not doc.is_rental_item:
        return

    settings = frappe.get_single("Equipment Rental Settings")

    if settings.rental_item_group:
        doc.item_group = settings.rental_item_group

    company = settings.default_company
    if company and (settings.rental_income_account or settings.rental_expense_account):
        row = None
        for d in doc.item_defaults:
            if d.company == company:
                row = d
                break
        if not row:
            row = doc.append("item_defaults", {})
            row.company = company

        if settings.rental_income_account:
            row.income_account = settings.rental_income_account
        if settings.rental_expense_account:
            row.expense_account = settings.rental_expense_account

    if settings.rental_item_tax_template:
        has_template = any(
            t.item_tax_template == settings.rental_item_tax_template for t in doc.taxes
        )
        if not has_template:
            doc.append("taxes", {"item_tax_template": settings.rental_item_tax_template})


def apply_job_type_item_defaults(doc, method=None):
    """Item validate() hook: a Job Type item is a bundle parent, not a
    stock item -- its own stock/maintenance is never tracked. Stock only
    moves at the component level via a Product Bundle (screws, nuts,
    scaffolding pieces, etc). Force is_stock_item off, and remind the
    user if no Product Bundle has been set up yet, since forgetting that
    step means the components' stock never gets decremented."""
    if not doc.get("is_job_type_item"):
        return

    doc.is_stock_item = 0

    if doc.name and not frappe.db.exists("Product Bundle", {"new_item_code": doc.name}):
        frappe.msgprint(
            "This is a Job Type item -- remember to create a Product Bundle "
            "for it (Selling > Product Bundle) listing its component items "
            "and quantities, or its stock will never be decremented.",
            title="Product Bundle Required",
            indicator="orange",
        )


def sync_job_type_item_names(doc, method=None):
    """Item on_update() hook: when a Job Type item is linked to a Job Type
    master record, mirror its Product Bundle components into that Job
    Type's item_names table, so the rate-card view and the real
    stock-movement source of truth (Product Bundle) never drift apart."""
    if not (doc.get("is_job_type_item") and doc.get("job_type")):
        return

    bundle_name = frappe.db.get_value("Product Bundle", {"new_item_code": doc.name}, "name")
    if not bundle_name:
        return

    bundle = frappe.get_doc("Product Bundle", bundle_name)
    job_type = frappe.get_doc("Job Type", doc.job_type)

    job_type.item_names = []
    for row in bundle.items:
        item_name, stock_uom = frappe.db.get_value(
            "Item", row.item_code, ["item_name", "stock_uom"]
        )
        job_type.append("item_names", {
            "item_code": row.item_code,
            "item_description": item_name,
            "unit": stock_uom,
            "quantity": row.qty,
        })

    job_type.flags.ignore_permissions = True
    job_type.save()


def sync_rental_equipment(doc, method=None):
    """Item on_update() hook: when Is Rental Item is ticked, ensure at
    least one Rental Equipment record exists for it (linked via its
    Billing Item field), so the physical-unit register isn't left
    disconnected from the Item master. Required fields we can't sensibly
    default (Equipment Category, Serial No) are left blank for the user
    to fill in -- this is a starter record, not a complete one."""
    if not doc.get("is_rental_item"):
        return

    if frappe.db.exists("Rental Equipment", {"item": doc.name}):
        return

    settings = frappe.get_single("Equipment Rental Settings")

    equipment = frappe.new_doc("Rental Equipment")
    equipment.naming_series = "EQP-.#####"
    equipment.equipment_name = doc.item_name or doc.name
    equipment.item = doc.name
    equipment.company = settings.default_company
    equipment.flags.ignore_mandatory = True
    equipment.insert(ignore_permissions=True)

    frappe.msgprint(
        f"A starter Rental Equipment record ({equipment.name}) was created for this "
        f"item -- remember to set its Equipment Category and Serial/Plate No.",
        title="Rental Equipment Created",
        indicator="blue",
    )
