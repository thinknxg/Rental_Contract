frappe.ui.form.on("Item", {
    is_job_type_item: function(frm) {
        // Job Type items are bundle parents: their own stock is never tracked
        if (frm.doc.is_job_type_item) {
            frm.set_value("is_stock_item", 0);
        }
    },
    is_stock_item: function(frm) {
        // Keep it off if someone re-ticks it while Job Type is still ticked
        if (frm.doc.is_job_type_item && frm.doc.is_stock_item) {
            frm.set_value("is_stock_item", 0);
            frappe.show_alert({
                message: __("Job Type items cannot maintain stock."),
                indicator: "orange",
            });
        }
    },
});
