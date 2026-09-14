frappe.ui.form.on('Hire Order', {
    refresh: function(frm) {
        if (frm.doc.docstatus !== 1) return;

        frm.add_custom_button("Sales Order", function() {
            frappe.model.open_mapped_doc({
                method: "equip_rental.equipment_rental.doctype.hire_order.hire_order.make_sales_order",
                frm: frm,
            });
        }, "Create");
    },
});
