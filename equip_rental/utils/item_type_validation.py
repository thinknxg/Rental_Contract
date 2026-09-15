import frappe

PLAIN_SALE_DEAL_TYPES = ("Material Sale", "Material Sale Order")
HIRE_DEAL_TYPES = ("Material Hire", "Material Hire Order", "Contract Hire", "Contract Hire Order")


def _is_rental_or_job_type(item_code):
    if not item_code:
        return None
    return frappe.db.get_value(
        "Item", item_code, ["is_rental_item", "is_job_type_item"], as_dict=True
    )


def validate_hire_only_items(doc, method=None):
    """Hire Order / Hire Order Contract / Rental Contract: every line item
    must be a rental item or a job type item."""
    fieldname = "item" if doc.doctype == "Rental Contract" else "item_code"

    for row in doc.items:
        item_code = row.get(fieldname)
        flags = _is_rental_or_job_type(item_code)
        if not item_code or not flags or not (flags.is_rental_item or flags.is_job_type_item):
            frappe.throw(
                f"Row #{row.idx}: only Rental or Job Type items can be added to "
                f"{doc.doctype}. '{item_code or '(blank)'}' is neither."
            )


def validate_sales_order_items(doc, method=None):
    """Sales Order: plain sale deal types may only use non-rental,
    non-job-type items; hire deal types may only use rental/job-type
    items -- mirroring the same rule enforced on Hire Order/Rental
    Contract directly."""
    deal_type = doc.get("custom_deal_type")

    if deal_type in PLAIN_SALE_DEAL_TYPES:
        for row in doc.items:
            flags = _is_rental_or_job_type(row.item_code)
            if flags and (flags.is_rental_item or flags.is_job_type_item):
                frappe.throw(
                    f"Row #{row.idx}: '{row.item_code}' is a Rental/Job Type item and "
                    f"cannot be added to a plain sale Sales Order."
                )

    elif deal_type in HIRE_DEAL_TYPES:
        for row in doc.items:
            flags = _is_rental_or_job_type(row.item_code)
            if not flags or not (flags.is_rental_item or flags.is_job_type_item):
                frappe.throw(
                    f"Row #{row.idx}: only Rental or Job Type items can be added to "
                    f"a {deal_type} Sales Order. '{row.item_code}' is neither."
                )
