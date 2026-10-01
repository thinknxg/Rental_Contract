# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days
from frappe.model.document import Document
from frappe.utils import flt


class JCR(Document):
    def validate(self):
        self.calculate_excess_amounts()

    def calculate_excess_amounts(self):
        # Mirrors jcr.js exactly: excess_days = actual days (erection to
        # dismantle) minus contract_days. Weekly = charge x (days / 7),
        # Monthly = charge x (days / 30), Days = charge x days.
        from frappe.utils import date_diff, getdate

        for item in self.items:
            excess_charge = flt(item.excess_charge)
            contract_days = flt(item.contract_days)
            actual_days = 0
            if item.custom_erection_date and item.custom_dismantle_date:
                actual_days = date_diff(
                    getdate(item.custom_dismantle_date), getdate(item.custom_erection_date)
                )
            excess_days = actual_days - contract_days
            if excess_days <= 0 or not excess_charge:
                item.excess_days = 0
                item.excess_amount = 0
                continue

            item.excess_days = excess_days
            if item.excess_period == "Weekly":
                item.excess_amount = (excess_days / 7) * excess_charge
            elif item.excess_period == "Monthly":
                item.excess_amount = (excess_days / 30) * excess_charge
            else:
                item.excess_amount = excess_days * excess_charge


@frappe.whitelist()
def make_sdv(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.jcr = source.name
        target.naming_series = "SDV-.#####"

    def update_item(source_row, target_row, source_parent):
        target_row.job_no = source_row.job_no
        target_row.description = source_row.job_description

    return get_mapped_doc("JCR", source_name, {
        "JCR": {
            "doctype": "SDV",
            "field_map": {"client_name": "customer"},
            "validation": {"docstatus": ["=", 1]},
        },
        "JCR Item": {
            "doctype": "SDV Item",
            "postprocess": update_item,
        },
    }, target_doc, post_process)


@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def post_process(source, target):
        target.jcr = source.name
        target.naming_series = frappe.get_meta("Sales Invoice").get_field("naming_series").options.split("\n")[0]
        target.ignore_pricing_rule = 1
        for source_row in source.items:
            _append_invoice_rows(source, target, source_row)

    # Items are added in post_process: each JCR item becomes a contract row
    # plus an excess row (only if there are excess days).
    return get_mapped_doc("JCR", source_name, {
        "JCR": {
            "doctype": "Sales Invoice",
            "field_map": {"client_name": "customer"},
            "validation": {"docstatus": ["=", 1]},
        },
    }, target_doc, post_process)


def _fmt_date(d):
    from frappe.utils import formatdate
    return formatdate(d, "dd-mm-yyyy")


def _append_invoice_rows(source, target, row):
    item_code = item_name = None
    uom = stock_uom = None
    conversion_factor = 1
    base_amount = 0
    if row.sales_order_item:
        so_row = frappe.db.get_value(
            "Sales Order Item", row.sales_order_item,
            ["item_code", "item_name", "amount", "uom", "stock_uom", "conversion_factor"], as_dict=True,
        )
        if so_row:
            item_code = so_row.item_code
            item_name = so_row.item_name
            base_amount = flt(so_row.amount)
            uom = so_row.uom
            stock_uom = so_row.stock_uom
            conversion_factor = flt(so_row.conversion_factor) or 1

    item_name = item_name or row.job_description
    qty = flt(row.qty) or 1
    contract_days = flt(row.contract_days)
    erection = row.custom_erection_date
    contract_to = add_days(erection, contract_days - 1) if erection and contract_days else None

    # Heading line (no serial number): JCR job no + item name @ project name
    project_label = source.project_name or ""
    if project_label:
        project_label = frappe.db.get_value("Project", project_label, "project_name") or project_label
    heading = "{0} {1} @ {2}".format(source.name, item_name or "", project_label).strip()

    if erection and contract_to:
        contract_text = "{0} to {1}={2:g} Days".format(_fmt_date(erection), _fmt_date(contract_to), contract_days)
    else:
        contract_text = row.job_description or ""

    # Title row: JCR no + item name @ project. No qty/rate/amount.
    target.append("items", {
        "item_code": item_code,
        "item_name": item_name,
        "uom": uom,
        "stock_uom": stock_uom,
        "conversion_factor": conversion_factor,
        "description": heading,
        "qty": 1,
        "rate": 0,
        "amount": 0,
        "price_list_rate": 0,
        "base_rate": 0,
        "base_amount": 0,
        "ignore_pricing_rule": 1,
        "jcr": source.name,
    })

    # Row 1: contract days. Qty x rate = Sales Order Item amount.
    contract_rate = base_amount / qty
    target.append("items", {
        "item_code": item_code,
        "item_name": item_name,
        "uom": uom,
        "stock_uom": stock_uom,
        "conversion_factor": conversion_factor,
        "description": contract_text,
        "qty": qty,
        "rate": contract_rate,
        "amount": base_amount,
        "price_list_rate": contract_rate,
        "base_rate": contract_rate,
        "base_amount": base_amount,
        "ignore_pricing_rule": 1,
        "jcr": source.name,
        "custom_locked_rate": contract_rate,
        "custom_locked_amount": base_amount,
        "contract_amount": base_amount,
        "contract_from_date": erection,
        "contract_to_date": contract_to,
        "contract_days": contract_days,
    })

    excess_days = flt(row.excess_days)
    excess_charge = flt(row.excess_charge)
    if excess_days <= 0 or not excess_charge or not contract_to:
        return

    # Row 2: excess days. Unit price = excess days x charge per day
    # (Weekly/Monthly divide days by 7/30 first, same as the JCR).
    # Amount = qty x unit price. Applies on the Sales Invoice only.
    if row.excess_period == "Weekly":
        unit_price = (excess_days / 7) * excess_charge
    elif row.excess_period == "Monthly":
        unit_price = (excess_days / 30) * excess_charge
    else:
        unit_price = excess_days * excess_charge
    excess_amount = qty * unit_price

    target.append("items", {
        "item_code": item_code,
        "item_name": item_name,
        "uom": uom,
        "stock_uom": stock_uom,
        "conversion_factor": conversion_factor,
        "description": "{0} to {1}={2:g} Days x {3:g}={4:g}".format(
            _fmt_date(add_days(contract_to, 1)), _fmt_date(row.custom_dismantle_date),
            excess_days, excess_charge, unit_price),
        "qty": qty,
        "rate": unit_price,
        "amount": excess_amount,
        "price_list_rate": unit_price,
        "base_rate": unit_price,
        "base_amount": excess_amount,
        "ignore_pricing_rule": 1,
        "jcr": source.name,
        "custom_locked_rate": unit_price,
        "custom_locked_amount": excess_amount,
        "excess_charge": excess_charge,
        "excess_days": excess_days,
        "excess_period": row.excess_period,
        "excess_amount": excess_amount,
    })


@frappe.whitelist()
def create_sales_invoice(source_name):
    # Builds the Sales Invoice via make_sales_invoice (same rate/amount logic,
    # proven correct server-side) and inserts it directly, instead of loading
    # it unsaved into the browser form. Loading an unsaved mapped doc lets
    # ERPNext's item_code change-trigger auto-refetch rate/tax from the
    # Item's default price, which overwrites our computed amount within a
    # second of the form rendering. Inserting server-side and only then
    # opening the saved record avoids that trigger firing at all.
    existing = _live_invoice(source_name)
    if existing:
        frappe.throw(frappe._("JCR {0} already has Sales Invoice {1}").format(source_name, existing))
    si = make_sales_invoice(source_name)
    si.insert()
    return si.name


def _live_invoice(jcr):
    rows = frappe.db.sql(
        """select si.name from `tabSales Invoice` si
           left join `tabSales Invoice Item` sii on sii.parent = si.name
           where si.docstatus < 2 and (si.jcr = %(j)s or sii.jcr = %(j)s) limit 1""",
        {"j": jcr},
    )
    return rows[0][0] if rows else None


def _is_invoiced(jcr):
    return bool(_live_invoice(jcr))


@frappe.whitelist()
def get_invoiceable_jcrs(jcr):
    """Other submitted JCRs of the same customer that have no live invoice."""
    customer = frappe.db.get_value("JCR", jcr, "client_name")
    rows = frappe.get_all(
        "JCR",
        filters={"docstatus": 1, "client_name": customer, "name": ["!=", jcr]},
        fields=["name", "sales_order", "project_name", "lpo_number"],
        order_by="creation",
    )
    return [r for r in rows if not _is_invoiced(r.name)]


@frappe.whitelist()
def create_sales_invoice_for_jcrs(jcrs):
    """One Sales Invoice for several JCRs of the same customer. The first
    JCR in the list is the one the user opened and becomes the header link."""
    import json

    if isinstance(jcrs, str):
        jcrs = json.loads(jcrs)
    jcrs = list(dict.fromkeys(jcrs))
    if len(jcrs) < 2:
        frappe.throw(frappe._("Select at least one more JCR"))

    customers = set()
    for name in jcrs:
        doc = frappe.db.get_value("JCR", name, ["docstatus", "client_name"], as_dict=True)
        if not doc or doc.docstatus != 1:
            frappe.throw(frappe._("JCR {0} must be submitted").format(name))
        existing = _live_invoice(name)
        if existing:
            frappe.throw(frappe._("JCR {0} already has Sales Invoice {1}").format(name, existing))
        customers.add(doc.client_name)
    if len(customers) > 1:
        frappe.throw(frappe._("All JCRs must belong to the same customer"))

    si = None
    for name in jcrs:
        si = make_sales_invoice(name, si)
    si.jcr = jcrs[0]
    si.insert()
    return si.name
