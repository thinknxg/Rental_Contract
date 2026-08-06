app_name = "equip_rental"
app_title = "Equipment Rental"
app_publisher = "Kreatao"
app_description = "Equipment rental management for ERPNext: internal usage, customer hire, portal and invoicing"
app_email = "hello@kreatao.com"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

# ------------------------------------------------------------------ assets
app_include_css = "/assets/equip_rental/css/equip_rental.css"
web_include_css = "/assets/equip_rental/css/rental_portal.css"
web_include_js = "/assets/equip_rental/js/rental_portal.js"

# ------------------------------------------------------------------ website
website_route_rules = [
    {"from_route": "/equipment/<path:name>", "to_route": "Rental Equipment"},
]

portal_menu_items = [
    {"title": "My Rentals", "route": "/my-rentals", "reference_doctype": "Rental Contract",
     "role": "Customer"},
    {"title": "Sub-Rental Orders", "route": "/supplier-rentals",
     "reference_doctype": "Sub Rental Order", "role": "Supplier"},
]

has_website_permission = {
    "Rental Contract": "equip_rental.utils.permissions.rental_contract_permission",
    "Sub Rental Order": "equip_rental.utils.permissions.sub_rental_permission",
}

permission_query_conditions = {
    "Rental Contract": "equip_rental.utils.permissions.contract_query_conditions",
}

# ------------------------------------------------------------------ install
after_install = "equip_rental.install.after_install"
after_migrate = "equip_rental.install.after_migrate"

# ------------------------------------------------------------------ documents
doc_events = {
    "Sales Invoice": {
        "on_submit": "equip_rental.utils.billing.on_sales_invoice_submit",
        "on_cancel": "equip_rental.utils.billing.on_sales_invoice_cancel",
    },
}

# ------------------------------------------------------------------ scheduler
scheduler_events = {
    "daily": [
        "equip_rental.tasks.update_contract_statuses",
        "equip_rental.tasks.expire_reservations",
        "equip_rental.tasks.notify_returns_due",
        "equip_rental.tasks.notify_document_expiry",
        "equip_rental.tasks.flag_maintenance_due",
    ],
    "cron": {
        "0 2 * * *": ["equip_rental.tasks.run_automatic_billing"],
    },
}

# ------------------------------------------------------------------ jinja
jinja = {
    "methods": [
        "equip_rental.utils.common.equipment_thumbnail",
        "equip_rental.utils.pricing.get_display_rate",
    ]
}
