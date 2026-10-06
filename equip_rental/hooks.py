app_name = "equip_rental"
app_title = "Equipment Rental"
app_publisher = "Kreatao"
app_description = "Equipment rental management for ERPNext: internal usage, customer hire, portal and invoicing"
app_email = "hello@kreatao.com"
app_license = "MIT"
required_apps = ["frappe/erpnext"]

# ------------------------------------------------------------------ assets
app_include_css = [
    "/assets/equip_rental/css/equip_rental.css",
    "/assets/equip_rental/css/theme_toggle.css",
]
app_include_js = ["/assets/equip_rental/js/theme_toggle.js"]
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
            [
                "dt",
                "not in",
                [
                    "Address",
                    "Contact",
                    "DocPerm",
                    "Custom DocPerm",
                    "DocShare"
                ]
            ]
        ]
    },
    {
        "dt": "Property Setter",
        "filters": [
            [
                "name",
                "in",
                [
                    "Cross Hire Order-naming_series-default",
                    "Cross Hire Order-naming_series-options",
                    "Cross Hire Receipt-naming_series-default",
                    "Cross Hire Receipt-naming_series-options",
                    "Hire Order Contract-naming_series-options",
                    "Hire Order-naming_series-options",
                    "JCR-naming_series-options",
                    "Quotation Item-amount-columns",
                    "Quotation Item-amount-in_list_view",
                    "Quotation Item-amount-insert_after",
                    "Quotation Item-contract_days-columns",
                    "Quotation Item-contract_days-in_list_view",
                    "Quotation Item-custom_breadth-columns",
                    "Quotation Item-custom_breadth-in_list_view",
                    "Quotation Item-custom_height-columns",
                    "Quotation Item-custom_height-in_list_view",
                    "Quotation Item-custom_length-columns",
                    "Quotation Item-custom_length-in_list_view",
                    "Quotation Item-description-columns",
                    "Quotation Item-description-in_list_view",
                    "Quotation Item-excess_charge-columns",
                    "Quotation Item-excess_charge-in_list_view",
                    "Quotation Item-excess_period-columns",
                    "Quotation Item-excess_period-in_list_view",
                    "Quotation Item-is_job_type_item-columns",
                    "Quotation Item-is_job_type_item-in_list_view",
                    "Quotation Item-item_code-columns",
                    "Quotation Item-item_code-in_list_view",
                    "Quotation Item-item_name-columns",
                    "Quotation Item-item_name-in_list_view",
                    "Quotation Item-main-field_order",
                    "Quotation Item-period-columns",
                    "Quotation Item-period-in_list_view",
                    "Quotation Item-qty-columns",
                    "Quotation Item-qty-in_list_view",
                    "Quotation Item-qty-insert_after",
                    "Quotation Item-rate-columns",
                    "Quotation Item-rate-in_list_view",
                    "Quotation Item-rate-insert_after",
                    "Quotation Item-rate-label",
                    "Quotation Item-rotation_qty-columns",
                    "Quotation Item-rotation_qty-in_list_view",
                    "Quotation Item-uom-columns",
                    "Quotation Item-uom-in_list_view",
                    "Quotation Item-uom-insert_after",
                    "Quotation-base_rounded_total-hidden",
                    "Rental Dispatch Note-naming_series-default",
                    "Rental Dispatch Note-naming_series-options",
                    "Rental Equipment-naming_series-default",
                    "Rental Equipment-naming_series-options",
                    "Rental Return Note-naming_series-default",
                    "Rental Return Note-naming_series-options",
                    "Sales Invoice Item-base_net_rate-precision",
                    "Sales Invoice Item-base_price_list_rate-precision",
                    "Sales Invoice Item-base_rate-precision",
                    "Sales Invoice Item-description-columns",
                    "Sales Invoice Item-description-in_list_view",
                    "Sales Invoice Item-discount_account-hidden",
                    "Sales Invoice Item-discount_account-mandatory_depends_on",
                    "Sales Invoice Item-main-field_order",
                    "Sales Invoice Item-net_rate-precision",
                    "Sales Invoice Item-price_list_rate-precision",
                    "Sales Invoice Item-rate-precision",
                    "Sales Invoice Item-uom-columns",
                    "Sales Invoice Item-uom-in_list_view",
                    "Sales Invoice-additional_discount_account-hidden",
                    "Sales Invoice-additional_discount_account-mandatory_depends_on",
                    "Sales Invoice-base_rounded_total-hidden",
                    "Sales Invoice-tax_id-hidden",
                    "Sales Invoice-tax_id-print_hide",
                    "Sales Order Item-amount-columns",
                    "Sales Order Item-amount-in_list_view",
                    "Sales Order Item-contract_days-columns",
                    "Sales Order Item-contract_days-in_list_view",
                    "Sales Order Item-contract_days-label",
                    "Sales Order Item-custom_breadth-columns",
                    "Sales Order Item-custom_breadth-in_list_view",
                    "Sales Order Item-custom_contract_days-columns",
                    "Sales Order Item-custom_contract_days-in_list_view",
                    "Sales Order Item-custom_height-columns",
                    "Sales Order Item-custom_height-in_list_view",
                    "Sales Order Item-custom_length-columns",
                    "Sales Order Item-custom_length-in_list_view",
                    "Sales Order Item-delivery_date-in_list_view",
                    "Sales Order Item-description-columns",
                    "Sales Order Item-description-in_list_view",
                    "Sales Order Item-excess_charge-columns",
                    "Sales Order Item-excess_charge-in_list_view",
                    "Sales Order Item-excess_period-columns",
                    "Sales Order Item-excess_period-in_list_view",
                    "Sales Order Item-is_job_type_item-columns",
                    "Sales Order Item-is_job_type_item-in_list_view",
                    "Sales Order Item-item_code-columns",
                    "Sales Order Item-item_code-in_list_view",
                    "Sales Order Item-item_code-label",
                    "Sales Order Item-item_code-reqd",
                    "Sales Order Item-item_name-columns",
                    "Sales Order Item-item_name-in_list_view",
                    "Sales Order Item-item_name-insert_after",
                    "Sales Order Item-job_no-in_list_view",
                    "Sales Order Item-main-field_order",
                    "Sales Order Item-period-columns",
                    "Sales Order Item-period-in_list_view",
                    "Sales Order Item-qty-columns",
                    "Sales Order Item-qty-in_list_view",
                    "Sales Order Item-rate-columns",
                    "Sales Order Item-rate-in_list_view",
                    "Sales Order Item-rate-label",
                    "Sales Order Item-uom-columns",
                    "Sales Order Item-uom-in_list_view",
                    "Sales Order-base_rounded_total-hidden",
                    "Sales Order-main-field_order",
                    "Sales Order-tax_id-hidden",
                    "Sales Order-tax_id-print_hide"
                ]
            ]
        ]
    },
    {
        "dt": "Workspace",
        "filters": [
            [
                "module",
                "=",
                "Equipment Rental"
            ]
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
    "Sales Invoice": "public/js/sales_invoice_return.js",
}
