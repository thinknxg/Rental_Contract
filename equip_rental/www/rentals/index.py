import frappe
from frappe.utils import cint, nowdate

no_cache = 1


def get_context(context):
    settings = frappe.get_cached_doc("Equipment Rental Settings")
    if not settings.enable_public_catalogue:
        frappe.throw(frappe._("The equipment catalogue is not available"),
                     frappe.PermissionError)

    args = frappe.form_dict
    category = args.get("category")
    search = args.get("search")
    from_date = args.get("from_date")
    to_date = args.get("to_date")

    filters = {"published": 1, "status": ["not in", ["Retired", "Out of Service"]]}
    if category:
        filters["equipment_category"] = category

    or_filters = None
    if search:
        or_filters = {"equipment_name": ["like", "%" + search + "%"],
                      "model": ["like", "%" + search + "%"]}

    equipment = frappe.get_all(
        "Rental Equipment", filters=filters, or_filters=or_filters,
        fields=["name", "equipment_name", "equipment_category", "model", "image",
                "route", "short_description", "status", "daily_rate", "weekly_rate",
                "monthly_rate", "hourly_rate", "company"],
        order_by="equipment_name asc", limit_page_length=60)

    if from_date and to_date:
        from equip_rental.utils.availability import is_available
        equipment = [e for e in equipment if is_available(e.name, from_date, to_date)]

    for row in equipment:
        row.currency = frappe.db.get_value("Company", row.company, "default_currency")

    context.equipment = equipment
    context.categories = frappe.get_all("Equipment Category", fields=["name"],
                                        order_by="name asc")
    context.settings = settings
    context.show_rates = cint(settings.show_rates_on_portal)
    context.allow_booking = cint(settings.allow_portal_booking)
    context.selected = {"category": category, "search": search,
                        "from_date": from_date or nowdate(), "to_date": to_date}
    context.title = settings.portal_heading or "Equipment for Hire"
    context.no_cache = 1
    return context
