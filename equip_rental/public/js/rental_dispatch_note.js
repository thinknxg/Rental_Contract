frappe.ui.form.on("Rental Dispatch Note", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button("Return Note", () => {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.dispatch_to_return.make_return_note_from_dispatch",
                    frm: frm,
                });
            }, "Create");
        }
    },
});
