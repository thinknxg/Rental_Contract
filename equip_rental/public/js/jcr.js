frappe.ui.form.on("JCR Item", {
    custom_erection_date: function(frm, cdt, cdn) { recalculate_row(frm, cdt, cdn); },
    custom_dismantle_date: function(frm, cdt, cdn) { recalculate_row(frm, cdt, cdn); },
    contract_days: function(frm, cdt, cdn) { recalculate_row(frm, cdt, cdn); },
    excess_charge: function(frm, cdt, cdn) { recalculate_row(frm, cdt, cdn); },
    excess_period: function(frm, cdt, cdn) { recalculate_row(frm, cdt, cdn); },
});

function recalculate_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if (!(row.custom_erection_date && row.custom_dismantle_date)) {
        return;
    }

    const erection = frappe.datetime.str_to_obj(row.custom_erection_date);
    const dismantle = frappe.datetime.str_to_obj(row.custom_dismantle_date);
    const actual_days = frappe.datetime.get_day_diff(dismantle, erection);
    if (actual_days <= 0) {
        return;
    }

    const contract_days = flt(row.contract_days);
    const excess_days = actual_days - contract_days;
    if (excess_days <= 0) {
        frappe.model.set_value(cdt, cdn, "excess_amount", 0);
        return;
    }

    const excess_charge = flt(row.excess_charge);
    let excess_amount;
    if (row.excess_period === "Weekly") {
        excess_amount = (excess_days / 7) * excess_charge;
    } else if (row.excess_period === "Monthly") {
        excess_amount = (excess_days / 30) * excess_charge;
    } else {
        excess_amount = excess_days * excess_charge;
    }

    frappe.model.set_value(cdt, cdn, "excess_amount", excess_amount);
}
