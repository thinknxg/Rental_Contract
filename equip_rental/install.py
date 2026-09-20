import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
    "Sales Invoice": [
        {"fieldname": "rental_contract", "label": "Rental Contract", "fieldtype": "Link",
         "options": "Rental Contract", "insert_after": "project", "read_only": 1,
         "no_copy": 1, "print_hide": 0},
        {"fieldname": "rental_period_from", "label": "Rental Period From", "fieldtype": "Date",
         "insert_after": "rental_contract", "read_only": 1, "depends_on": "rental_contract"},
        {"fieldname": "rental_period_to", "label": "Rental Period To", "fieldtype": "Date",
         "insert_after": "rental_period_from", "read_only": 1, "depends_on": "rental_contract"},
    ],
    "Sales Invoice Item": [
        {"fieldname": "rental_equipment", "label": "Rental Equipment", "fieldtype": "Link",
         "options": "Rental Equipment", "insert_after": "item_name", "read_only": 1},
    ],
    "Purchase Invoice": [
        {"fieldname": "cross_hire_order", "label": "Cross Hire Order",
         "fieldtype": "Link", "options": "Cross Hire Order", "insert_after": "project",
         "read_only": 1, "no_copy": 1},
        {"fieldname": "cross_hire_reconciliation", "label": "Cross Hire Reconciliation",
         "fieldtype": "Link", "options": "Cross Hire Invoice Reconciliation",
         "insert_after": "cross_hire_order", "read_only": 1, "no_copy": 1},
    ],
    "Item": [
        {"fieldname": "is_rental_item", "label": "Is Rental Item", "fieldtype": "Check",
         "insert_after": "is_stock_item"},
        {"fieldname": "is_job_type_item", "label": "Is Job Type Item", "fieldtype": "Check",
         "insert_after": "is_rental_item"},
        {"fieldname": "section_break_jt_rates", "label": "Rates", "fieldtype": "Section Break",
         "insert_after": "is_job_type_item", "depends_on": "is_job_type_item"},
        {"fieldname": "contract_rate_per_sqm", "label": "Contract Rate / SQM", "fieldtype": "Currency",
         "insert_after": "section_break_jt_rates"},
        {"fieldname": "rate_type", "label": "Rate Type", "fieldtype": "Select",
         "options": "Daily\nWeekly\nMonthly\nLumpsum", "insert_after": "contract_rate_per_sqm"},
        {"fieldname": "column_break_jt_rates", "fieldtype": "Column Break",
         "insert_after": "rate_type"},
        {"fieldname": "rate_per_sqm", "label": "Rate / SQM", "fieldtype": "Currency",
         "insert_after": "column_break_jt_rates"},
        {"fieldname": "lumpsum_rate", "label": "Lumpsum Rate", "fieldtype": "Currency",
         "insert_after": "rate_per_sqm"},
        {"fieldname": "section_break_jt_items", "label": "Item Names", "fieldtype": "Section Break",
         "insert_after": "lumpsum_rate", "depends_on": "is_job_type_item"},
        {"fieldname": "job_type_item_names", "label": "Item Names", "fieldtype": "Table",
         "options": "Job Type Item Name", "insert_after": "section_break_jt_items"},
    ],
    "Sales Order Item": [
        {"fieldname": "column_break_so_dim", "fieldtype": "Column Break",
         "insert_after": "contract_days"},
        {"fieldname": "length", "label": "Length", "fieldtype": "Float",
         "insert_after": "column_break_so_dim"},
        {"fieldname": "width", "label": "Width", "fieldtype": "Float",
         "insert_after": "length"},
        {"fieldname": "height", "label": "Height", "fieldtype": "Float",
         "insert_after": "width"},
        {"fieldname": "area", "label": "Area", "fieldtype": "Float",
         "read_only": 1, "insert_after": "height"},
    ],
    "Customer": [
        {"fieldname": "default_rate_card", "label": "Default Rental Rate Card",
         "fieldtype": "Link", "options": "Rental Rate Card", "insert_after": "default_price_list"},
    ],
    "Supplier": [
        {"fieldname": "is_rental_supplier", "label": "Supplies Rental Equipment",
         "fieldtype": "Check", "insert_after": "supplier_group"},
    ],
}

ROLES = [
    {"role_name": "Rental Manager", "desk_access": 1},
    {"role_name": "Rental User", "desk_access": 1},
]

CHARGE_TYPES = [
    {"charge_name": "Delivery", "charge_basis": "Fixed"},
    {"charge_name": "Collection", "charge_basis": "Fixed"},
    {"charge_name": "Damage Recovery", "charge_basis": "Fixed"},
    {"charge_name": "Cleaning", "charge_basis": "Fixed"},
    {"charge_name": "Fuel", "charge_basis": "Fixed"},
    {"charge_name": "Late Return Surcharge", "charge_basis": "Percent of Rental"},
    {"charge_name": "Operator", "charge_basis": "Per Unit"},
]


def after_install():
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)
    _create_roles()
    _create_charge_types()
    _set_defaults()
    frappe.db.commit()


def after_migrate():
    create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)


def _create_roles():
    for role in ROLES:
        if not frappe.db.exists("Role", role["role_name"]):
            frappe.get_doc(dict(doctype="Role", **role)).insert(ignore_permissions=True)


def _create_charge_types():
    for charge in CHARGE_TYPES:
        if not frappe.db.exists("Rental Charge Type", charge["charge_name"]):
            frappe.get_doc(dict(doctype="Rental Charge Type", **charge)).insert(
                ignore_permissions=True)


def _set_defaults():
    settings = frappe.get_single("Equipment Rental Settings")
    if not settings.default_company:
        settings.default_company = frappe.defaults.get_defaults().get("company")
    if not settings.rental_item_group and frappe.db.exists("Item Group", "Services"):
        settings.rental_item_group = "Services"
    if not settings.portal_heading:
        settings.portal_heading = "Equipment for Hire"
    settings.flags.ignore_mandatory = True
    settings.save(ignore_permissions=True)
