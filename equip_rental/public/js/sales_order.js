frappe.ui.form.on("Sales Order", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button("Dispatch Note", () => {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.sales_order_to_dispatch.make_dispatch_note",
                    frm: frm,
                });
            }, "Create");

            frm.add_custom_button("Rental Contract", () => {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.sales_order_to_contract.make_rental_contract",
                    frm: frm,
                });
            }, "Create");
        }
    },
});

frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        toggle_hire_item_grid(frm);
    },
    custom_deal_type: function(frm) {
        toggle_hire_item_grid(frm);
    },
});

function toggle_hire_item_grid(frm) {
    const is_hire = ["Material Hire Order", "Contract Hire Order"].includes(frm.doc.custom_deal_type);
    const grid = frm.fields_dict.items.grid;

    grid.update_docfield_property("item_code", "in_list_view", is_hire ? 0 : 1);
    grid.update_docfield_property("delivery_date", "in_list_view", is_hire ? 0 : 1);
    grid.update_docfield_property("job_no", "in_list_view", is_hire ? 1 : 0);
    grid.update_docfield_property("contract_days", "in_list_view", is_hire ? 1 : 0);
    grid.update_docfield_property("description", "in_list_view", is_hire ? 1 : 0);
    grid.update_docfield_property("description", "label", is_hire ? "Job Description" : "Description");
    grid.update_docfield_property("amount", "label", is_hire ? "Contract Amount" : "Amount");

    grid.refresh();
}

frappe.ui.form.on("Sales Order", {
    onload: function(frm) {
        if (!frm.__original_calculate_taxes_and_totals) {
            frm.__original_calculate_taxes_and_totals = frm.cscript.calculate_taxes_and_totals;
        }
        toggle_core_totals(frm);
    },
    refresh: function(frm) {
        toggle_core_totals(frm);
        recalculate_all_so_items(frm);
    },
    custom_deal_type: function(frm) {
        toggle_core_totals(frm);
        frm.fields_dict.items.grid.refresh();
        recalculate_all_so_items(frm);
    },
});

frappe.ui.form.on("Sales Order Item", {
    qty: function(frm, cdt, cdn) { recalculate_so_item(frm, cdt, cdn); },
    rate: function(frm, cdt, cdn) { recalculate_so_item(frm, cdt, cdn); },
    contract_days: function(frm, cdt, cdn) { recalculate_so_item(frm, cdt, cdn); },
});

function toggle_core_totals(frm) {
    const hire_types = ["Material Hire Order", "Contract Hire Order"];
    if (hire_types.includes(frm.doc.custom_deal_type)) {
        frm.cscript.calculate_taxes_and_totals = function() {
            // disabled: core's Qty x Rate totals would overwrite our
            // Qty x Rate x Days totals for hire deal types
        };
    } else if (frm.__original_calculate_taxes_and_totals) {
        frm.cscript.calculate_taxes_and_totals = frm.__original_calculate_taxes_and_totals;
    }
}

function recalculate_so_item(frm, cdt, cdn) {
    const hire_types = ["Material Hire Order", "Contract Hire Order"];
    if (!hire_types.includes(frm.doc.custom_deal_type)) {
        return; // let core ERPNext handle Qty x Rate as normal
    }

    const row = locals[cdt][cdn];
    const multiplier = row.contract_days ? row.contract_days : 1;
    const correct_amount = flt(row.qty) * flt(row.rate) * flt(multiplier);

    row.amount = correct_amount;
    row.net_amount = correct_amount;
    row.base_amount = correct_amount * (frm.doc.conversion_rate || 1);
    row.base_net_amount = row.base_amount;

    refresh_field("amount", cdn, "items");
    recalculate_so_totals(frm);
}

function recalculate_all_so_items(frm) {
    const hire_types = ["Material Hire Order", "Contract Hire Order"];
    if (!hire_types.includes(frm.doc.custom_deal_type)) return;
    (frm.doc.items || []).forEach(row => recalculate_so_item(frm, row.doctype, row.name));
}

function recalculate_so_totals(frm) {
    let total = 0;
    (frm.doc.items || []).forEach(row => { total += flt(row.amount); });

    const conversion_rate = frm.doc.conversion_rate || 1;

    frm.set_value("total", total);
    frm.set_value("net_total", total);
    frm.set_value("base_total", total * conversion_rate);
    frm.set_value("base_net_total", total * conversion_rate);
    frm.set_value("grand_total", total);
    frm.set_value("rounded_total", Math.round(total));
    frm.set_value("base_grand_total", total * conversion_rate);
    frm.set_value("base_rounded_total", Math.round(total * conversion_rate));
}

frappe.ui.form.on("Sales Order", {
    po_no: function(frm) {
        frm.set_value("lpo_no", frm.doc.po_no);
    },
    po_date: function(frm) {
        frm.set_value("lpo_date", frm.doc.po_date);
    },
    refresh: function(frm) {
        if (frm.doc.po_no && !frm.doc.lpo_no) {
            frm.set_value("lpo_no", frm.doc.po_no);
        }
        if (frm.doc.po_date && !frm.doc.lpo_date) {
            frm.set_value("lpo_date", frm.doc.po_date);
        }
    },
});
