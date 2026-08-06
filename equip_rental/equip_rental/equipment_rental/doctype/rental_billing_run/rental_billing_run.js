frappe.ui.form.on("Rental Billing Run", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Run Billing"), () => {
			frappe.confirm(
				__("Generate billing documents for {0} to {1}?",
					[frm.doc.period_from, frm.doc.period_to]),
				() => {
					frm.call({ doc: frm.doc, method: "execute", freeze: true,
						freeze_message: __("Billing rental contracts...") })
						.then((r) => {
							frm.reload_doc();
							if (r.message) {
								frappe.msgprint(__("{0} documents created", [r.message.created]));
							}
						});
				});
		}).addClass("btn-primary");
	},
});
