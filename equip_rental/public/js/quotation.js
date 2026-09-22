frappe.ui.form.on('Quotation', {
    party_name: function(frm) {
        if (frm.doc.quotation_to === 'Customer' && frm.doc.party_name) {
            frappe.db.get_value('Customer', frm.doc.party_name, 'tax_id', (r) => {
                if (r && r.tax_id) {
                    frm.set_value('customer_trn', r.tax_id);
                }
            });
        } else {
            frm.set_value('customer_trn', '');
        }
    },

    custom_deal_type: function(frm) {
        toggle_core_totals(frm);
        frm.fields_dict.items.grid.refresh();
        recalculate_all_items(frm);
    },

    onload: function(frm) {
        if (!frm.__original_calculate_taxes_and_totals) {
            frm.__original_calculate_taxes_and_totals = frm.cscript.calculate_taxes_and_totals;
        }
        toggle_core_totals(frm);
    },
    refresh: function(frm) {
        toggle_core_totals(frm);
    },
});

frappe.ui.form.on('Quotation Item', {
    qty: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    rate: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    rotation_qty: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_rate_type: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_length: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_breadth: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_height: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_no_of_locations: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
    custom_duration: function(frm, cdt, cdn) { recalculate_item(frm, cdt, cdn); },
});

function recalculate_item(frm, cdt, cdn) {
    const hire_types = ["Material Hire", "Contract Hire"];
    if (!hire_types.includes(frm.doc.custom_deal_type)) {
        return; // let core ERPNext handle Qty x Rate as normal
    }

    const row = locals[cdt][cdn];
    let correct_amount;

    if (frm.doc.custom_deal_type === "Contract Hire") {
        correct_amount = calculate_contract_hire_amount(row);
    } else {
        // Material Hire: existing rotation_qty based calculation
        const multiplier = row.rotation_qty ? row.rotation_qty : 1;
        correct_amount = flt(row.qty) * flt(row.rate) * flt(multiplier);
    }

    row.amount = correct_amount;
    row.net_amount = correct_amount;
    row.base_amount = correct_amount * (frm.doc.conversion_rate || 1);
    row.base_net_amount = row.base_amount;

    refresh_field("amount", cdn, "items");
    recalculate_totals(frm);
}

function calculate_contract_hire_amount(row) {
    const length = flt(row.custom_length);
    const breadth = flt(row.custom_breadth);
    const height = flt(row.custom_height);
    const locations = flt(row.custom_no_of_locations);
    const duration = flt(row.custom_duration);
    const qty = flt(row.qty);
    const rate = flt(row.rate);

    let amount = 0;

    switch (row.custom_rate_type) {
        case "M3":
            row.custom_calculated_volume = length * breadth * height * locations;
            amount = row.custom_calculated_volume * rate * duration;
            break;
        case "SQM":
            row.custom_calculated_volume = length * breadth * locations;
            amount = row.custom_calculated_volume * rate * duration;
            break;
        case "Nos":
            amount = qty * rate;
            break;
        case "Day":
        case "Month":
            amount = qty * rate * duration;
            break;
        case "Lumpsum":
            amount = rate;
            break;
        default:
            amount = 0;
    }

    refresh_field("custom_calculated_volume", row.name, "items");
    return amount;
}

function recalculate_all_items(frm) {
    (frm.doc.items || []).forEach(row => recalculate_item(frm, row.doctype, row.name));
}

function recalculate_totals(frm) {
    // Manually sum grand totals WITHOUT calling core's calculate_taxes_and_totals,
    // since that function recalculates every item's amount as Qty x Rate and
    // would silently overwrite our Hire-specific custom amounts.
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

function toggle_core_totals(frm) {
    const hire_types = ["Material Hire", "Contract Hire"];
    if (hire_types.includes(frm.doc.custom_deal_type)) {
        frm.cscript.calculate_taxes_and_totals = function() {
            // disabled: core's Qty x Rate totals would overwrite our
            // Qty x Rate x Duration totals for hire deal types
        };
    } else if (frm.__original_calculate_taxes_and_totals) {
        frm.cscript.calculate_taxes_and_totals = frm.__original_calculate_taxes_and_totals;
    }
}
