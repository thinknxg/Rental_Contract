import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
from frappe.website.website_generator import WebsiteGenerator


class RentalEquipment(WebsiteGenerator):
    website = frappe._dict(
        template="templates/generators/rental_equipment.html",
        condition_field="published",
        page_title_field="equipment_name",
    )

    def validate(self):
        self.set_route()
        self.sync_category_defaults()
        self.validate_rates()

    def set_route(self):
        if self.published and not self.route:
            self.route = "equipment/" + self.scrub(
                "{0}-{1}".format(self.equipment_name, self.name))

    def scrub(self, text):
        return frappe.scrub(text).replace("_", "-")

    def sync_category_defaults(self):
        if not self.equipment_category:
            return
        category = frappe.get_cached_doc("Equipment Category", self.equipment_category)
        if not self.meter_type or self.meter_type == "None":
            self.meter_type = category.meter_type or "None"
        if not self.rate_card and category.default_rate_card:
            self.rate_card = category.default_rate_card
        if not self.item and category.default_item:
            self.item = category.default_item

    def validate_rates(self):
        if self.ownership == "Sub-Rented" and not self.supplier:
            frappe.throw(_("Select the Supplier for sub-rented equipment"))
        if not self.rate_card and not any(
                flt(self.get(f)) for f in
                ("hourly_rate", "daily_rate", "weekly_rate", "monthly_rate")):
            frappe.msgprint(
                _("No rate card or rate is set for {0}. Contracts will need a manual rate.")
                .format(self.name), indicator="orange", alert=True)

    def set_status(self, status, contract=None, available_from=None):
        self.db_set("status", status, update_modified=False)
        self.db_set("current_contract", contract, update_modified=False)
        if available_from:
            self.db_set("available_from", available_from, update_modified=False)

    def get_context(self, context):
        context.no_cache = 1
        context.parents = [{"name": _("Equipment"), "route": "/rentals"}]
        context.category_doc = frappe.get_cached_doc(
            "Equipment Category", self.equipment_category)
        settings = frappe.get_cached_doc("Equipment Rental Settings")
        context.settings = settings
        context.show_rates = cint(settings.show_rates_on_portal)
        context.allow_booking = cint(settings.allow_portal_booking)
        context.related = frappe.get_all(
            "Rental Equipment",
            filters={"published": 1, "equipment_category": self.equipment_category,
                     "name": ["!=", self.name]},
            fields=["equipment_name", "route", "image", "daily_rate"],
            limit_page_length=4)
        return context


@frappe.whitelist()
def get_equipment_rate(equipment, rate_basis="Day", customer=None):
    from equip_rental.utils.pricing import get_rate
    rate, row = get_rate(equipment, rate_basis, customer)
    return {"rate": rate,
            "min_billable_units": (row or {}).get("min_billable_units") if row else 1}
