import frappe
from frappe import _
from frappe.utils import cint, getdate, nowdate

from equip_rental.utils.availability import get_available_equipment, is_available
from equip_rental.utils.common import (get_customer_for_user, get_settings,
                                       get_supplier_for_user)
from equip_rental.utils.pricing import get_billable_units, get_rate, line_amount


@frappe.whitelist(allow_guest=True)
def catalogue(equipment_category=None, from_date=None, to_date=None, search=None,
              limit=40):
    settings = get_settings()
    if not settings.enable_public_catalogue:
        frappe.throw(_("The equipment catalogue is not published"), frappe.PermissionError)

    filters = {"published": 1, "status": ["not in", ["Retired", "Out of Service"]]}
    if equipment_category:
        filters["equipment_category"] = equipment_category
    or_filters = None
    if search:
        or_filters = {"equipment_name": ["like", "%" + search + "%"],
                      "model": ["like", "%" + search + "%"]}

    rows = frappe.get_all(
        "Rental Equipment", filters=filters, or_filters=or_filters,
        fields=["name", "equipment_name", "equipment_category", "model", "image",
                "route", "short_description", "daily_rate", "weekly_rate",
                "monthly_rate", "status"],
        order_by="equipment_name asc", limit_page_length=cint(limit))

    if from_date and to_date:
        rows = [r for r in rows if is_available(r.name, from_date, to_date)]

    if not settings.show_rates_on_portal:
        for row in rows:
            row.daily_rate = row.weekly_rate = row.monthly_rate = None
    return rows


@frappe.whitelist(allow_guest=True)
def check_availability(equipment, from_date, to_date):
    available = is_available(equipment, from_date, to_date)
    return {"available": available, "equipment": equipment,
            "from_date": from_date, "to_date": to_date}


@frappe.whitelist(allow_guest=True)
def quote(equipment, from_date, to_date, rate_basis="Day", qty=1):
    rate, row = get_rate(equipment, rate_basis, get_customer_for_user())
    min_units = (row or {}).get("min_billable_units") if row else 1
    units = get_billable_units(from_date, to_date, rate_basis, min_units or 1)
    return {"rate": rate, "rate_basis": rate_basis, "units": units,
            "amount": line_amount(units, qty, rate)}


@frappe.whitelist(allow_guest=True)
def request_booking(equipment=None, equipment_category=None, from_date=None, to_date=None,
                    contact_person=None, contact_email=None, contact_mobile=None,
                    site_address=None, notes=None, qty=1):
    settings = get_settings()
    if not settings.allow_portal_booking:
        frappe.throw(_("Online booking requests are disabled"))
    if not (from_date and to_date):
        frappe.throw(_("Select a hire period"))
    if getdate(to_date) < getdate(from_date):
        frappe.throw(_("The end date cannot be before the start date"))

    if frappe.session.user == "Guest" and not contact_email:
        frappe.throw(_("Enter an email address so we can reply"))

    reservation = frappe.new_doc("Rental Reservation")
    reservation.reservation_type = "Customer Rental"
    reservation.company = settings.default_company
    reservation.customer = get_customer_for_user()
    reservation.from_date = getdate(from_date)
    reservation.to_date = getdate(to_date)
    reservation.contact_person = contact_person
    reservation.contact_email = contact_email or (
        frappe.session.user if frappe.session.user != "Guest" else None)
    reservation.contact_mobile = contact_mobile
    reservation.site_address = site_address
    reservation.notes = notes
    reservation.source = "Portal"

    category = equipment_category
    if equipment and not category:
        category = frappe.db.get_value("Rental Equipment", equipment,
                                       "equipment_category")
    reservation.append("items", {
        "equipment": equipment, "equipment_category": category, "qty": cint(qty) or 1,
        "rate_basis": settings.default_rate_basis or "Day",
    })
    reservation.flags.ignore_permissions = True
    reservation.insert()

    if settings.portal_enquiry_recipient:
        frappe.sendmail(
            recipients=[settings.portal_enquiry_recipient],
            subject=_("New rental request {0}").format(reservation.name),
            message=_("A rental request was submitted from the website: {0}").format(
                reservation.name),
            reference_doctype="Rental Reservation", reference_name=reservation.name,
            delayed=True)

    return {"name": reservation.name,
            "message": _("Thank you. Your request {0} has been received.").format(
                reservation.name)}


@frappe.whitelist()
def my_contracts(status=None):
    customer = get_customer_for_user()
    if not customer:
        return []
    filters = {"customer": customer, "docstatus": 1}
    if status:
        filters["status"] = status
    return frappe.get_all(
        "Rental Contract", filters=filters,
        fields=["name", "start_date", "expected_end_date", "status", "billing_cycle",
                "estimated_total", "total_billed", "currency"],
        order_by="start_date desc")


@frappe.whitelist()
def request_off_hire(rental_contract, requested_date, equipment=None, notes=None):
    settings = get_settings()
    if not settings.allow_portal_off_hire:
        frappe.throw(_("Off-hire requests are disabled"))

    customer = get_customer_for_user()
    contract_customer = frappe.db.get_value("Rental Contract", rental_contract, "customer")
    if not customer or customer != contract_customer:
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    request = frappe.new_doc("Rental Off Hire Request")
    request.rental_contract = rental_contract
    request.equipment = equipment
    request.requested_date = getdate(requested_date)
    request.notes = notes
    request.source = "Portal"
    request.flags.ignore_permissions = True
    request.insert()
    return {"name": request.name}


@frappe.whitelist()
def supplier_orders():
    supplier = get_supplier_for_user()
    if not supplier:
        return []
    return frappe.get_all(
        "Sub Rental Order", filters={"supplier": supplier, "docstatus": ["<", 2]},
        fields=["name", "from_date", "to_date", "status", "total_amount", "currency"],
        order_by="from_date desc")
