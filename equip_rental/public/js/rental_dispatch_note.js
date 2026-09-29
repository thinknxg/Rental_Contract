frappe.ui.form.on("Rental Dispatch Note", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.sales_order) {
            frm.add_custom_button(__("Return Note"), function() {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.rental_dispatch_to_return.make_return_note",
                    frm: frm,
                });
            }, __("Create"));

            frm.add_custom_button(__("JCR"), function() {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.sales_order_to_jcr.make_jcr",
                    source_name: frm.doc.sales_order,
                });
            }, __("Create"));
        }
    },
});
