import frappe

LEAD_TO_QUOTATION = {
    "Material Sale": "Material Sale",
    "Material Hire": "Material Hire",
    "Contract Hire": "Contract Hire",
}

QUOTATION_TO_SALES_ORDER = {
    "Material Sale": "Material Sale Order",
    "Material Hire": "Material Hire Order",
    "Contract Hire": "Contract Hire Order",
}

SALES_ORDER_TO_INVOICE = {
    "Material Sale Order": "Sale Invoice",
    "Material Hire Order": "Hire Invoice",
    "Contract Hire Order": "Contract Invoice",
}


def map_deal_type(value, mapping, doctype_label=""):
    """Look up value in mapping; raise a clear error if it's missing."""
    if value not in mapping:
        frappe.throw(
            f"No Deal Type mapping found for '{value}'"
            f"{' on ' + doctype_label if doctype_label else ''}. "
            f"Valid source values are: {', '.join(mapping.keys())}"
        )
    return mapping[value]
