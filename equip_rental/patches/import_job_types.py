# Copyright (c) 2026, ThinknXG and contributors
# For license information, please see license.txt

import frappe

JOB_DESCRIPTIONS = [
    "Lift Shaft Internal Access Scaffolding-Cuplok System",
    "Pipe Rack",
    "Internal Access Scaffolding (Pit Stage Scaffolding)",
    "Internal Access Scaffolding (First Stage Scaffolding)",
    "Internal Access Scaffolding (Second Stage Scaffolding)",
    "Internal Access Scaffolding (Third Stage Scaffolding)",
    "Internal Access Scaffolding (Forth Stage Scaffolding)",
    "Internal Access Scaffolding (Fifth Stage Scaffolding)",
    "Internal Access Scaffolding (Final Stage Scaffolding)",
    "Internal Birdcage Access Scaffolding-Cuplok System",
    "External Hanging Access Scaffolding- Cuplok System",
    "External Staircase Access Scaffolding- CUPLOK SYSTEM",
    "External Access Scaffolding- CUPLOK SYSTEM",
    "External Tower Access Scaffolding- Cuplok System",
    "Manpower Supply",
    "Internal Access Scaffolding- CUPLOK SYSTEM",
    "Aluminium Mobile Tower Scaffolding",
    "Internal Cantilever Access Scaffolding- Cuplok System",
    "Support Tower",
    "External Cantilever Access Scaffolding - CUPLOK SYSTEM",
    "Scaffolding Materials for Hire",
    "Modification / Rectification Works",
    "Tower Access Scaffolding - CUPLOK SYSTEM",
    "External Birdcage Access Scaffolding-Cuplok System",
    "External & Internal Access Scaffolding - CUPLOK SYSTEM",
    "Internal Hanging Access Scaffolding - TUBE AND COUPLER",
    "Scaffolding Loading Platform - Cuplok System",
    "Scaffolding with Light Fixing",
    "Ladder with Light Fixing",
    "Paint Damaged Electric Pole Post Maintenance",
]


def execute():
    for description in JOB_DESCRIPTIONS:
        if frappe.db.exists("Job Type", {"job_description": description}):
            continue
        doc = frappe.new_doc("Job Type")
        doc.job_description = description
        doc.insert(ignore_permissions=True)

    frappe.db.commit()
    print(f"Imported {len(JOB_DESCRIPTIONS)} Job Type records (skipping existing).")
