frappe.ui.form.on("Rental Dispatch Note", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.rental_contract) {
            frm.add_custom_button(__("JCR"), function() {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.sales_order_to_jcr.make_jcr",
                    source_name: frm.doc.rental_contract,
                });
            }, __("Create"));
        }
    },
});
