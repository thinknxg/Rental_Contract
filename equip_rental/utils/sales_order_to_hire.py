import frappe

ITEM_FIELDS = ["job_no", "description", "contract_days", "qty"]
SERVICE_FIELDS = ["job_no", "service", "rate", "qty", "amount"]

HEADER_FIELDS = [
    "customer", "site_and_project", "payment_terms_code", "payment_terms",
    "revision_no", "lpo_no", "lpo_date", "update_lpo_in_deliveries",
    "contract_from", "contract_to", "rent_start_from", "description_2",
]


def _build_items(source_items, item_doctype):
    rows = []
    for row in source_items:
        new_row = {"doctype": item_doctype}
        for f in ITEM_FIELDS:
            new_row[f] = row.get(f)
        new_row["contract_rate"] = row.get("rate")
        new_row["contract_amount"] = row.get("amount")
        rows.append(new_row)
    return rows


def _build_services(source_services, service_doctype):
    rows = []
    for row in source_services:
        new_row = {"doctype": service_doctype}
        for f in SERVICE_FIELDS:
            new_row[f] = row.get(f)
        rows.append(new_row)
    return rows


def create_hire_order_on_submit(doc, method=None):
    if doc.custom_deal_type not in ("Material Hire Order", "Contract Hire Order"):
        return

    is_contract = doc.custom_deal_type == "Contract Hire Order"
    target_doctype = "Hire Order Contract" if is_contract else "Hire Order"
    item_doctype = "Hire Order Contract Item" if is_contract else "Hire Order Item"
    service_doctype = "Hire Order Contract Service" if is_contract else "Hire Order Service"
    link_fieldname = "custom_hire_order_contract" if is_contract else "custom_hire_order"

    new_doc = frappe.new_doc(target_doctype)
    new_doc.date = doc.transaction_date
    new_doc.status = doc.custom_status
    new_doc.status_date = doc.status_date
    for f in HEADER_FIELDS:
        new_doc.set(f, doc.get(f))

    new_doc.items = []
    for row in _build_items(doc.items, item_doctype):
        new_doc.append("items", row)

    new_doc.services = []
    for row in _build_services(doc.services, service_doctype):
        new_doc.append("services", row)

    new_doc.insert(ignore_permissions=True)
    new_doc.submit()

    frappe.db.set_value("Sales Order", doc.name, link_fieldname, new_doc.name)
