frappe.ui.form.on("Equipment Rental Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Open Public Catalogue"), () => {
			window.open("/rentals");
		});
	},
});
