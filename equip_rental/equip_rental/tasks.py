import frappe
from frappe.utils import add_days, getdate, nowdate

from equip_rental.utils.billing import create_invoice_for_contract
from equip_rental.utils.common import get_settings
from equip_rental.utils.pricing import period_end_for_cycle, next_billing_date


def update_contract_statuses():
    """Move contracts through Scheduled -> Active -> Overdue."""
    today = getdate(nowdate())
    for row in frappe.get_all("Rental Contract",
                              filters={"docstatus": 1,
                                       "status": ["not in", ["Closed", "Cancelled"]]},
                              fields=["name", "start_date", "expected_end_date",
                                      "is_open_ended", "status"]):
        status = row.status
        if getdate(row.start_date) > today:
            status = "Scheduled"
        elif not row.is_open_ended and row.expected_end_date \
                and getdate(row.expected_end_date) < today:
            status = "Overdue"
        else:
            status = "Active"
        if status != row.status:
            frappe.db.set_value("Rental Contract", row.name, "status", status,
                                update_modified=False)
    frappe.db.commit()


def expire_reservations():
    today = getdate(nowdate())
    for name in frappe.get_all("Rental Reservation",
                               filters={"status": ["in", ["Draft", "Confirmed"]],
                                        "to_date": ["<", today]}, pluck="name"):
        frappe.db.set_value("Rental Reservation", name, "status", "Expired",
                            update_modified=False)
    frappe.db.commit()


def notify_returns_due():
    settings = get_settings()
    days = int(settings.return_due_reminder_days or 0)
    if not days:
        return
    target = add_days(nowdate(), days)
    contracts = frappe.get_all(
        "Rental Contract",
        filters={"docstatus": 1, "status": ["in", ["Active", "Scheduled"]],
                 "expected_end_date": target, "is_open_ended": 0},
        fields=["name", "customer_name", "expected_end_date", "owner"])
    for contract in contracts:
        _notify(contract.owner, "Rental Contract", contract.name,
                "Return due on {0} for {1}".format(contract.expected_end_date,
                                                   contract.customer_name or contract.name))


def notify_document_expiry():
    settings = get_settings()
    days = int(settings.document_expiry_reminder_days or 0)
    if not days:
        return
    target = add_days(nowdate(), days)
    rows = frappe.db.sql("""
        select d.parent as equipment, d.document_type, d.expiry_date, e.owner
        from `tabRental Equipment Document` d
        inner join `tabRental Equipment` e on e.name = d.parent
        where d.expiry_date = %s""", target, as_dict=True)
    for row in rows:
        _notify(row.owner, "Rental Equipment", row.equipment,
                "{0} for {1} expires on {2}".format(row.document_type, row.equipment,
                                                    row.expiry_date))


def flag_maintenance_due():
    today = getdate(nowdate())
    rows = frappe.get_all(
        "Rental Equipment",
        filters={"status": ["not in", ["Retired", "In Maintenance"]],
                 "next_maintenance_date": ["<=", today]},
        fields=["name", "owner", "next_maintenance_date"])
    for row in rows:
        _notify(row.owner, "Rental Equipment", row.name,
                "Maintenance due for {0}".format(row.name))


def run_automatic_billing():
    """Nightly billing for contracts whose next billing date has arrived."""
    today = getdate(nowdate())
    settings = get_settings()
    contracts = frappe.get_all(
        "Rental Contract",
        filters={"docstatus": 1, "auto_billing": 1,
                 "status": ["in", ["Active", "Overdue"]],
                 "billing_cycle": ["!=", "On Return"],
                 "next_billing_date": ["<=", today]},
        fields=["name", "billing_cycle", "next_billing_date", "start_date"])

    for contract in contracts:
        try:
            period_from = getdate(contract.next_billing_date)
            period_to = period_end_for_cycle(period_from, contract.billing_cycle,
                                             settings.bill_calendar_month)
            if period_to and period_to >= today:
                period_to = add_days(today, 0)
            create_invoice_for_contract(contract.name, period_from, period_to)
            frappe.db.set_value(
                "Rental Contract", contract.name, "next_billing_date",
                next_billing_date(add_days(period_to, 1), contract.billing_cycle,
                                  settings.bill_calendar_month) or add_days(period_to, 1),
                update_modified=False)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(frappe.get_traceback(),
                             "Rental auto-billing failed: {0}".format(contract.name))


def _notify(user, doctype, name, subject):
    if not user or user == "Administrator":
        return
    notification = frappe.new_doc("Notification Log")
    notification.subject = subject
    notification.for_user = user
    notification.document_type = doctype
    notification.document_name = name
    notification.type = "Alert"
    notification.insert(ignore_permissions=True)
