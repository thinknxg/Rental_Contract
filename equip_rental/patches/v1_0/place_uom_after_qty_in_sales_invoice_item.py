import json

import frappe

DT = "Sales Invoice Item"


def execute():
    cf = frappe.get_doc("Customize Form")
    cf.doc_type = DT
    cf.fetch_to_customize()

    rows = list(cf.fields)
    qty = next((r for r in rows if r.fieldname == "qty"), None)
    uom = next((r for r in rows if r.fieldname == "uom"), None)
    if not (qty and uom):
        return

    rows.remove(uom)
    rows.insert(rows.index(qty) + 1, uom)
    for i, r in enumerate(rows, start=1):
        r.idx = i
    cf.fields = rows

    uom.in_list_view = 1
    uom.columns = 1
    cf.save_customization()

    # Saved per-user grid layouts override the doctype, so drop them for
    # Sales Invoice (only the Items grid layout, nothing else).
    for row in frappe.db.sql(
        "select user, data from `__UserSettings` where doctype=%s",
        ("Sales Invoice",),
        as_dict=True,
    ):
        data = json.loads(row.data or "{}")
        grid = data.get("GridView") or {}
        if DT in grid:
            grid.pop(DT)
            data["GridView"] = grid
            frappe.db.sql(
                "update `__UserSettings` set data=%s where doctype=%s and user=%s",
                (json.dumps(data), "Sales Invoice", row.user),
            )

    frappe.clear_cache(doctype=DT)
    frappe.clear_cache(doctype="Sales Invoice")
