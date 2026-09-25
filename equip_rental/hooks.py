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

website_context = {
}

portal_menu_items = [
    {"title": "My Rentals", "route": "/my-rentals", "reference_doctype": "Rental Contract",
     "role": "Customer"},
    {"title": "Cross Hire Orders", "route": "/supplier-rentals",
     "reference_doctype": "Cross Hire Order", "role": "Supplier"},
]

has_website_permission = {
    "Rental Contract": "equip_rental.utils.permissions.rental_contract_permission",
    "Cross Hire Order": "equip_rental.utils.permissions.cross_hire_permission",
}

permission_query_conditions = {
    "Rental Contract": "equip_rental.utils.permissions.contract_query_conditions",
}

# ------------------------------------------------------------------ fixtures
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["name", "in", [
                "Quotation-revision_of",
                "Quotation-project",
                "Quotation-subject",
                "Quotation-customer_trn",
                "Quotation Item-rotation_qty",
                "Quotation Item-period",
                "Lead-custom_deal_type",
                "Quotation-custom_deal_type",
                "Sales Order-custom_deal_type",
                "Sales Invoice-custom_deal_type",
                "Rental Dispatch Note-sales_order",
                "Rental Return Note-rental_dispatch_note",
                "Rental Contract-sales_order",
                "Sales Order Item-job_no",
                "Sales Order Item-contract_days",
                "Sales Order-section_break_hire",
                "Sales Order-custom_status",
                "Sales Order-status_date",
                "Sales Order-column_break_hire_hdr",
                "Sales Order-site_and_project",
                "Sales Order-section_break_hire_terms",
                "Sales Order-payment_terms_code",
                "Sales Order-payment_terms",
                "Sales Order-column_break_hire_lpo",
                "Sales Order-revision_no",
                "Sales Order-lpo_no",
                "Sales Order-lpo_date",
                "Sales Order-update_lpo_in_deliveries",
                "Sales Order-section_break_hire_dates",
                "Sales Order-contract_from",
                "Sales Order-contract_to",
                "Sales Order-column_break_hire_rent",
                "Sales Order-rent_start_from",
                "Sales Order-description_2",
                "Sales Order-services",
                "Sales Order-custom_hire_order",
                "Sales Order-custom_hire_order_contract",
                "JCR Item-custom_erection_date",
                "JCR Item-custom_dismantle_date",
            ]]
        ]
    }
]

# ------------------------------------------------------------------ overrides
override_whitelisted_methods = {
    "equip_rental.utils.sales_order_to_dispatch.make_dispatch_note": "equip_rental.utils.sales_order_to_dispatch.make_dispatch_note",
    "erpnext.crm.doctype.lead.lead.make_quotation": "equip_rental.utils.deal_type_overrides.make_quotation",
    "erpnext.selling.doctype.quotation.quotation.make_sales_order": "equip_rental.utils.deal_type_overrides.make_sales_order",
    "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice": "equip_rental.utils.deal_type_overrides.make_sales_invoice",
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
    "Sales Order": {
        "validate": [
            "equip_rental.utils.deal_type_overrides.recalculate_hire_amounts_so",
            "equip_rental.utils.item_type_validation.validate_sales_order_items",
            "equip_rental.utils.sales_order_to_hire.calculate_so_item_area",
        ],
        "on_submit": "equip_rental.utils.sales_order_to_hire.create_hire_order_on_submit",
    },
    "JCR": {
        "validate": "equip_rental.utils.jcr_excess.calculate_excess",
    },
    "Item": {
        "validate": [
            "equip_rental.utils.rental_item_defaults.apply_rental_item_defaults",
            "equip_rental.utils.rental_item_defaults.apply_job_type_item_defaults",
        ],
        "on_update": [
            "equip_rental.utils.rental_item_defaults.sync_rental_equipment",
            "equip_rental.utils.rental_item_defaults.sync_job_type_item_names",
        ],
    },
    "Quotation": {
        "validate": "equip_rental.utils.deal_type_overrides.recalculate_hire_amounts",
    },
    "Hire Order": {
        "validate": "equip_rental.utils.item_type_validation.validate_hire_only_items",
        "on_submit": "equip_rental.utils.rental_stock_movement.issue_stock_on_hire_order_submit",
    },
    "Hire Order Contract": {
        "validate": "equip_rental.utils.item_type_validation.validate_hire_only_items",
        "on_submit": "equip_rental.utils.rental_stock_movement.issue_stock_on_hire_order_submit",
    },
    "Rental Contract": {
        "validate": "equip_rental.utils.item_type_validation.validate_hire_only_items",
    },
    "Hire Return Note": {
        "on_submit": "equip_rental.utils.rental_stock_movement.receive_stock_on_hire_return_submit",
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
        "equip_rental.utils.cross_hire.accrue_cross_hire_costs",
        "equip_rental.utils.cross_hire.alert_idle_cross_hire",
        "equip_rental.utils.cross_hire.alert_off_hire_notice_due",
        "equip_rental.utils.cross_hire.alert_orphan_cross_hire",
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


doctype_js = {
    "Quotation": "public/js/quotation.js",
    "Item": "public/js/item.js",
    "Hire Order": "public/js/hire_order.js",
    "Sales Order": "public/js/sales_order.js",
    "Rental Dispatch Note": "public/js/rental_dispatch_note.js",
    "JCR": "public/js/jcr.js",
}
