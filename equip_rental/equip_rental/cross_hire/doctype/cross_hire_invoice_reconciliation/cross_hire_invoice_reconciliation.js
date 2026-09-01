frappe.ui.form.on("Cross Hire Invoice Reconciliation", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.cross_hire_order
			&& frm.doc.period_from && frm.doc.period_to) {
			frm.add_custom_button(__("Pull Expected Charges"), () => {
				frm.call({ doc: frm.doc, method: "pull_expected", freeze: true })
					.then(() => frm.reload_doc());
			}).addClass("btn-primary");
		}

		if (frm.doc.docstatus === 1 && frm.doc.purchase_invoice) {
			frm.add_custom_button(__("Purchase Invoice"), () => {
				frappe.set_route("Form", "Purchase Invoice", frm.doc.purchase_invoice);
			}, __("View"));
		}

		if (frm.doc.total_variance) {
			const over = frm.doc.total_variance > 0;
			frm.dashboard.set_headline_alert(
				`<span class="indicator ${over ? "red" : "green"}">
					${__("Vendor claim is off by")} ${format_currency(frm.doc.total_variance)}
				</span>`);
		}
	},
});
