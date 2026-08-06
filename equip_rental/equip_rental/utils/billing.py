import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

from equip_rental.utils.common import get_billing_item, get_settings
from equip_rental.utils.pricing import get_billable_units, line_amount


def get_item_period(item, contract, period_from, period_to):
    """Chargeable window for one contract line inside a billing period."""
    start = getdate(item.charge_from)
    if item.last_billed_upto:
        start = max(start, add_days(getdate(item.last_billed_upto), 1))
    start = max(start, getdate(period_from))

    end_candidates = [getdate(period_to)]
    for value in (item.off_rent_date, item.charge_upto, contract.actual_end_date):
        if value:
            end_candidates.append(getdate(value))
    if not contract.is_open_ended and contract.expected_end_date:
        end_candidates.append(getdate(contract.expected_end_date))
    end = min(end_candidates)

    return start, end


def get_billable_lines(contract, period_from, period_to):
    """Compute the invoiceable lines for a contract within a period."""
    lines = []
    for item in contract.items:
        if item.item_status == "Cancelled":
            continue
        start, end = get_item_period(item, contract, period_from, period_to)
        if end < start:
            continue
        units = get_billable_units(start, end, item.rate_basis, item.min_billable_units)
        if not units:
            continue
        amount = line_amount(units, item.qty, item.rate, item.discount_percent)
        lines.append(frappe._dict({
            "row": item, "period_from": start, "period_to": end,
            "units": units, "amount": amount,
        }))
    return lines


@frappe.whitelist()
def create_invoice_for_contract(contract, period_from, period_to, submit=0):
    """Create a draft ERPNext Sales Invoice for one billing period."""
    contract = frappe.get_doc("Rental Contract", contract)
    settings = get_settings()

    if contract.docstatus != 1:
        frappe.throw(_("Only submitted contracts can be billed"))
    if contract.contract_type == "Internal Use":
        return create_internal_recharge(contract.name, period_from, period_to)

    lines = get_billable_lines(contract, period_from, period_to)
    pending_charges = [c for c in contract.charges if not c.is_invoiced]

    if not lines and not pending_charges:
        return None

    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = contract.customer
    invoice.company = contract.company
    invoice.currency = contract.currency
    invoice.posting_date = nowdate()
    invoice.due_date = None
    invoice.project = contract.project
    invoice.cost_center = contract.cost_center
    invoice.rental_contract = contract.name
    invoice.rental_period_from = getdate(period_from)
    invoice.rental_period_to = getdate(period_to)
    if contract.price_list:
        invoice.selling_price_list = contract.price_list
    if contract.taxes_and_charges:
        invoice.taxes_and_charges = contract.taxes_and_charges

    for line in lines:
        item = line.row
        billing_item = item.item or get_billing_item(
            frappe.get_cached_doc("Rental Equipment", item.equipment))
        row = invoice.append("items", {})
        row.item_code = billing_item
        row.qty = flt(line.units) * (flt(item.qty) or 1)
        row.rate = flt(item.rate)
        row.rental_equipment = item.equipment
        row.cost_center = contract.cost_center
        row.description = _("{0} | {1} rental {2} to {3}").format(
            item.equipment_name or item.equipment, item.rate_basis,
            line.period_from, line.period_to)
        if item.discount_percent:
            row.discount_percentage = flt(item.discount_percent)

    for charge in pending_charges:
        charge_item = charge.item or frappe.db.get_value(
            "Rental Charge Type", charge.charge_type, "item")
        if not charge_item:
            continue
        row = invoice.append("items", {})
        row.item_code = charge_item
        row.qty = 1
        row.rate = flt(charge.amount)
        row.cost_center = contract.cost_center
        row.description = charge.description or charge.charge_type

    if not invoice.items:
        return None

    invoice.flags.ignore_permissions = True
    invoice.set_missing_values()
    invoice.insert()

    if int(submit or 0) or settings.auto_submit_invoices:
        invoice.submit()

    _mark_billed(contract, lines, pending_charges, invoice)
    return invoice.name


def _mark_billed(contract, lines, charges, invoice):
    for line in lines:
        item = line.row
        item.db_set("last_billed_upto", line.period_to, update_modified=False)
        item.db_set("billed_units", flt(item.billed_units) + flt(line.units),
                    update_modified=False)
        item.db_set("billed_amount", flt(item.billed_amount) + flt(line.amount),
                    update_modified=False)
    for charge in charges:
        charge.db_set("is_invoiced", 1, update_modified=False)
        charge.db_set("sales_invoice", invoice.name, update_modified=False)

    log = contract.append("invoices", {})
    log.sales_invoice = invoice.name
    log.period_from = invoice.rental_period_from
    log.period_to = invoice.rental_period_to
    log.amount = invoice.grand_total
    log.status = invoice.status or ("Draft" if invoice.docstatus == 0 else "Unpaid")
    contract.total_billed = flt(contract.total_billed) + flt(invoice.grand_total)
    contract.flags.ignore_validate_update_after_submit = True
    contract.save(ignore_permissions=True)


@frappe.whitelist()
def create_internal_recharge(contract, period_from, period_to):
    """Internal usage does not invoice - it recharges the using cost center."""
    contract = frappe.get_doc("Rental Contract", contract)
    settings = get_settings()

    if not settings.book_internal_usage:
        _mark_internal_billed(contract, period_from, period_to)
        return None

    if not (settings.internal_income_account and settings.internal_expense_account):
        frappe.throw(_("Set the internal recharge accounts in Equipment Rental Settings"))

    lines = get_billable_lines(contract, period_from, period_to)
    total = sum(flt(line.amount) for line in lines)
    if not total:
        return None

    entry = frappe.new_doc("Journal Entry")
    entry.voucher_type = "Journal Entry"
    entry.company = contract.company
    entry.posting_date = nowdate()
    entry.user_remark = _("Internal equipment usage {0}: {1} to {2}").format(
        contract.name, period_from, period_to)

    entry.append("accounts", {
        "account": settings.internal_expense_account,
        "debit_in_account_currency": total,
        "cost_center": contract.cost_center,
        "project": contract.project,
    })
    entry.append("accounts", {
        "account": settings.internal_income_account,
        "credit_in_account_currency": total,
        "cost_center": contract.cost_center,
    })
    entry.flags.ignore_permissions = True
    entry.insert()
    if settings.auto_submit_invoices:
        entry.submit()

    for line in lines:
        line.row.db_set("last_billed_upto", line.period_to, update_modified=False)
        line.row.db_set("billed_amount", flt(line.row.billed_amount) + flt(line.amount),
                        update_modified=False)

    log = contract.append("invoices", {})
    log.journal_entry = entry.name
    log.period_from = getdate(period_from)
    log.period_to = getdate(period_to)
    log.amount = total
    log.status = "Recharged"
    contract.total_billed = flt(contract.total_billed) + total
    contract.flags.ignore_validate_update_after_submit = True
    contract.save(ignore_permissions=True)
    return entry.name


def _mark_internal_billed(contract, period_from, period_to):
    for line in get_billable_lines(contract, period_from, period_to):
        line.row.db_set("last_billed_upto", line.period_to, update_modified=False)


def on_sales_invoice_submit(doc, method=None):
    _sync_contract_invoice_status(doc)


def on_sales_invoice_cancel(doc, method=None):
    if not doc.get("rental_contract"):
        return
    frappe.db.sql("""update `tabRental Contract Invoice`
        set status = 'Cancelled' where sales_invoice = %s""", doc.name)


def _sync_contract_invoice_status(doc):
    if not doc.get("rental_contract"):
        return
    frappe.db.sql("""update `tabRental Contract Invoice`
        set status = %s where sales_invoice = %s""", (doc.status or "Unpaid", doc.name))
