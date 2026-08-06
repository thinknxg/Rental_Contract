frappe.ui.form.on("Rental Reservation", {
	refresh(frm) {
		if (frm.doc.docstatus === 2 || frm.is_new()) return;

		if (frm.doc.status === "Draft") {
			frm.add_custom_button(__("Confirm"), () => {
				frm.set_value("status", "Confirmed");
				frm.save();
			}).addClass("btn-primary");
		}

		if (["Draft", "Confirmed"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Rental Contract"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.equipment_rental.doctype.rental_reservation.rental_reservation.make_rental_contract",
					frm: frm,
				});
			}, __("Create"));

			frm.add_custom_button(__("Cancel Reservation"), () => {
				frm.set_value("status", "Cancelled");
				frm.save();
			});
		}
	},
});
