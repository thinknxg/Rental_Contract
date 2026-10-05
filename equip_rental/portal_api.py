"""Read-only helpers for the /portal SPA. No business logic: creation, submit,
cancel and mapping reuse existing doctype controllers and mappers. All reads go
through frappe.get_list / has_permission so Frappe permissions always apply."""
import frappe
from frappe import _
from frappe.utils import cint, flt, get_fullname

STAFF = {"Rental Manager", "Rental User", "System Manager"}
HIRE = ["Material Hire Order", "Contract Hire Order"]


@frappe.whitelist(allow_guest=True)
def me():
    user = frappe.session.user
    roles = frappe.get_roles() if user != "Guest" else []
    return {"user": user, "full_name": get_fullname(user) if user != "Guest" else "",
            "roles": roles, "is_staff": bool(STAFF & set(roles))}


def _count(doctype, filters):
    # permission-aware; avoids SQL-function strings that newer Frappe rejects
    return len(frappe.get_list(doctype, filters=filters, pluck="name", limit_page_length=0))


@frappe.whitelist()
def portal_summary():
    recent = lambda dt, extra=(): frappe.get_list(  # noqa: E731
        dt, fields=["name", "docstatus", "modified"] + list(extra),
        order_by="modified desc", limit_page_length=5)
    return {
        "cards": {
            "sales_orders_awaiting_dispatch": _count("Sales Order", {
                "docstatus": 1, "custom_deal_type": ["in", HIRE], "per_delivered": ["<", 100]}),
            "dispatch_drafts": _count("Rental Dispatch Note", {"docstatus": 0}),
            "dispatches_submitted": _count("Rental Dispatch Note", {"docstatus": 1}),
            "jcr_drafts": _count("JCR", {"docstatus": 0}),
            "jcr_submitted": _count("JCR", {"docstatus": 1}),
            "return_notes_submitted": _count("Rental Return Note", {"docstatus": 1}),
        },
        "recent": {
            "Rental Dispatch Note": recent("Rental Dispatch Note", ["customer"]),
            "JCR": recent("JCR", ["client_name"]),
            "Rental Return Note": recent("Rental Return Note", ["customer"]),
        },
    }


@frappe.whitelist()
def outstanding_returns(limit=50):
    """Read-only; mirrors the remaining-qty rule in Rental Return Note.validate_returnable."""
    notes = frappe.get_list(
        "Rental Dispatch Note", filters={"docstatus": 1, "delivery_note": ["is", "set"]},
        fields=["name", "customer", "rental_contract", "delivery_note", "dispatch_datetime"],
        order_by="dispatch_datetime desc", limit_page_length=cint(limit))
    out = []
    for n in notes:
        rows = frappe.get_all("Delivery Note Item", filters={"parent": n.delivery_note},
                              fields=["item_code", "item_name", "qty", "returned_qty"])
        items = [{"item_code": r.item_code, "item_name": r.item_name,
                  "dispatched": flt(r.qty), "returned": abs(flt(r.returned_qty)),
                  "outstanding": flt(r.qty) - abs(flt(r.returned_qty))} for r in rows]
        if any(i["outstanding"] > 0 for i in items):
            n["items"] = items
            out.append(n)
    return out


@frappe.whitelist()
def related_documents(doctype, name):
    if not frappe.has_permission(doctype, "read", name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    def rel(dt, filters):
        return [{"doctype": dt, "name": r.name, "docstatus": r.docstatus}
                for r in frappe.get_list(dt, filters=filters, fields=["name", "docstatus"],
                                         limit_page_length=50)]

    docs = []
    if doctype == "Sales Order":
        dispatches = rel("Rental Dispatch Note", {"rental_contract": name})
        jcrs = rel("JCR", {"sales_order": name})
        docs += dispatches + jcrs + rel("Rental Return Note", {"rental_contract": name})
        for d in dispatches:
            dn = frappe.db.get_value("Rental Dispatch Note", d["name"], "delivery_note")
            if dn and frappe.has_permission("Delivery Note", "read", dn):
                docs.append({"doctype": "Delivery Note", "name": dn, "docstatus": 1})
        if jcrs:
            docs += rel("Sales Invoice", {"jcr": ["in", [j["name"] for j in jcrs]]})
        so = frappe.get_doc("Sales Order", name)
        for f, dt in (("custom_hire_order", "Hire Order"), ("custom_hire_order_contract", "Hire Order Contract")):
            if so.get(f) and frappe.has_permission(dt, "read", so.get(f)):
                docs.append({"doctype": dt, "name": so.get(f), "docstatus": 1})
    elif doctype == "Quotation":
        sos = frappe.get_all("Sales Order Item", filters={"prevdoc_docname": name},
                             pluck="parent", distinct=True)
        if sos:
            docs += rel("Sales Order", {"name": ["in", sos]})
    elif doctype == "Rental Dispatch Note":
        d = frappe.db.get_value(doctype, name, ["rental_contract", "delivery_note"], as_dict=True)
        docs.append({"doctype": "Sales Order", "name": d.rental_contract, "docstatus": 1})
        if d.delivery_note:
            docs.append({"doctype": "Delivery Note", "name": d.delivery_note, "docstatus": 1})
        docs += rel("Rental Return Note", {"rental_dispatch_note": name})
    elif doctype == "JCR":
        so = frappe.db.get_value("JCR", name, "sales_order")
        if so:
            docs.append({"doctype": "Sales Order", "name": so, "docstatus": 1})
        docs += rel("SDV", {"jcr": name}) + rel("Sales Invoice", {"jcr": name})
    return docs
