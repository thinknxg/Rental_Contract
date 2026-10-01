import json

import frappe

DT = "Sales Invoice Item"


def execute():
    cf = frappe.get_doc("Customize Form")
    cf.doc_type = DT
    cf.fetch_to_customize()

    rows = list(cf.fields)
    item = next((r for r in rows if r.fieldname == "item_code"), None)
    desc = next((r for r in rows if r.fieldname == "description"), None)
    if not (item and desc):
        return

    # Move description to sit right after item_code (so before qty)
    rows.remove(desc)
    rows.insert(rows.index(item) + 1, desc)
    for i, r in enumerate(rows, start=1):
        r.idx = i
    cf.fields = rows

    desc.in_list_view = 1
    desc.columns = 4
    cf.save_customization()

    # Drop saved per-user Items grid layouts, which override the doctype
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
