import frappe


def execute():
    cf = frappe.get_doc("Customize Form")
    cf.doc_type = "Sales Order Item"
    cf.fetch_to_customize()

    field_map = {f.fieldname: f for f in cf.fields if f.fieldname}
    field_map["description"].in_list_view = 1
    field_map["contract_days"].in_list_view = 1

    desired_order = ["item_code", "item_name", "description", "contract_days", "qty", "rate", "amount"]
    new_fields = [field_map[fn] for fn in desired_order if fn in field_map]
    remaining = [f for f in cf.fields if f.fieldname not in desired_order]
    cf.fields = new_fields + remaining

    for i, f in enumerate(cf.fields, start=1):
        f.idx = i

    cf.save_customization()
    frappe.db.commit()
