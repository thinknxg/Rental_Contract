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
        frappe.model.set_value(cdt, cdn, "excess_days", 0);
        frappe.model.set_value(cdt, cdn, "excess_amount", 0);
        return;
    }
    frappe.model.set_value(cdt, cdn, "excess_days", excess_days);

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

frappe.ui.form.on("JCR", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Sales Invoice"), function() {
                frappe.call({
                    method: "equip_rental.equipment_rental.doctype.jcr.jcr.create_sales_invoice",
                    args: { source_name: frm.doc.name },
                    freeze: true,
                    freeze_message: __("Creating Sales Invoice..."),
                    callback: function(r) {
                        if (r.message) {
                            frappe.set_route("Form", "Sales Invoice", r.message);
                        }
                    },
                });
            }, __("Create"));
        }
    },
});


frappe.ui.form.on("JCR", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Multiple JCRs"), function() {
                open_multi_jcr_dialog(frm);
            }, __("Create"));
        }
    },
});

function open_multi_jcr_dialog(frm) {
    frappe.call({
        method: "equip_rental.equipment_rental.doctype.jcr.jcr.get_invoiceable_jcrs",
        args: { jcr: frm.doc.name },
        callback: function(r) {
            const rows = r.message || [];
            if (!rows.length) {
                frappe.msgprint(__("No other submitted, uninvoiced JCRs found for {0}", [frm.doc.client_name]));
                return;
            }
            const fields = [{
                fieldtype: "HTML",
                fieldname: "info",
                options: "<p>" + __("This JCR is included. Tick the others to invoice together.") + "</p>",
            }];
            rows.forEach(function(row, i) {
                const parts = [row.name, row.sales_order, row.project_name, row.lpo_number].filter(Boolean);
                fields.push({ fieldtype: "Check", fieldname: "jcr_" + i, label: parts.join(" | ") });
            });
            const d = new frappe.ui.Dialog({
                title: __("Invoice multiple JCRs"),
                fields: fields,
                primary_action_label: __("Create Sales Invoice"),
                primary_action: function(values) {
                    const picked = [frm.doc.name];
                    rows.forEach(function(row, i) {
                        if (values["jcr_" + i]) picked.push(row.name);
                    });
                    if (picked.length < 2) {
                        frappe.msgprint(__("Tick at least one other JCR"));
                        return;
                    }
                    frappe.call({
                        method: "equip_rental.equipment_rental.doctype.jcr.jcr.create_sales_invoice_for_jcrs",
                        args: { jcrs: picked },
                        freeze: true,
                        callback: function(res) {
                            if (res.message) {
                                d.hide();
                                frappe.set_route("Form", "Sales Invoice", res.message);
                            }
                        },
                    });
                },
            });
            d.show();
        },
    });
}
