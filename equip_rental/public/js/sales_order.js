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
