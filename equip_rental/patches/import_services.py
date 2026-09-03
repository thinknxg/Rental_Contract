# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe

SERVICE_DESCRIPTIONS = [
    "Suspended Cradle Operators Training",
    "RTA- Metro Rail No Objection Certificate (Apply)",
    "Painting",
    "Fixing of LED Lights",
    "Fixing of Faucets",
    "Fixing of Towel Bar",
    "Tiling Work",
    "Painting",
    "PCR Test of Scaffolders",
    "WJ2 Blasting",
    "Scaffolding and Hydroblasting",
    "Blasting and Painting",
    "Demolish",
    "SCAFFOLDING CONTRACT",
    "NET COVERING",
    "THIRD PARTY INSPECTION",
]


def execute():
    for description in SERVICE_DESCRIPTIONS:
        if frappe.db.exists("Service", {"description": description}):
            continue
        doc = frappe.new_doc("Service")
        doc.description = description
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    print(f"Imported {len(SERVICE_DESCRIPTIONS)} Service records (skipping existing duplicates like 'Painting').")
