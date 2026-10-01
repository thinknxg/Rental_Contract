import frappe
from frappe import _

from equip_rental.utils.rental_dispatch_to_return import make_return_note as make_from_dispatch


@frappe.whitelist()
def make_return_note(source_name, target_doc=None):
    si = frappe.get_doc("Sales Invoice", source_name)
    if si.docstatus != 1:
        frappe.throw(_("Sales Invoice must be submitted"))

    sales_order = None
    if si.get("jcr"):
        sales_order = frappe.db.get_value("JCR", si.jcr, "sales_order")
    if not sales_order:
        sales_order = next((i.sales_order for i in si.items if i.get("sales_order")), None)
    if not sales_order:
        frappe.throw(_("Could not find a Sales Order for this invoice, so no Dispatch Note can be traced"))

    dispatch = frappe.get_all(
        "Rental Dispatch Note",
        filters={"sales_order": sales_order, "docstatus": 1},
        fields=["name", "delivery_note"],
        order_by="creation desc",
        limit=1,
    )
    if not dispatch or not dispatch[0].delivery_note:
        frappe.throw(_("No submitted Dispatch Note found for Sales Order {0}").format(sales_order))

    return make_from_dispatch(dispatch[0].name)
