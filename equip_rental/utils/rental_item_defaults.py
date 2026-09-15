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
