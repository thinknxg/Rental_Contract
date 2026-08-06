frappe.ui.form.on("Sub Rental Order", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		if (!frm.doc.purchase_invoice) {
			frm.add_custom_button(__("Purchase Invoice"), () => {
				frm.call({ doc: frm.doc, method: "make_purchase_invoice", freeze: true })
					.then((r) => {
						if (r.message) frappe.set_route("Form", "Purchase Invoice", r.message);
					});
			}, __("Create"));
		}

		["Received", "Returned"].forEach((status) => {
			if (frm.doc.status !== status) {
				frm.add_custom_button(__("Mark {0}", [__(status)]), () => {
					frm.set_value("status", status);
					frm.save("Update");
				}, __("Status"));
			}
		});
	},
});
