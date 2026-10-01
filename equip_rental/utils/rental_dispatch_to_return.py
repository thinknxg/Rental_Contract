import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def make_return_note(source_name, target_doc=None):
    rdn = frappe.get_doc("Rental Dispatch Note", source_name)
    if rdn.docstatus != 1 or not rdn.delivery_note:
        frappe.throw(_("Dispatch Note must be submitted and have a Delivery Note"))

    doc = frappe.new_doc("Rental Return Note")
    doc.rental_contract = rdn.rental_contract
    doc.rental_dispatch_note = rdn.name
    doc.customer = rdn.customer
    doc.company = rdn.company

    rows = frappe.get_all(
        "Delivery Note Item",
        filters={"parent": rdn.delivery_note},
        fields=["item_code", "item_name", "warehouse", "qty", "returned_qty"],
    )
    for r in rows:
        remaining = flt(r.qty) - abs(flt(r.returned_qty))
        if remaining <= 0:
            continue
        doc.append("items", {
            "item_code": r.item_code,
            "item_name": r.item_name,
            "warehouse": r.warehouse,
            "qty_to_return": remaining,
        })

    if not doc.items:
        frappe.throw(_("Everything on Delivery Note {0} has already been returned").format(rdn.delivery_note))
    return doc
