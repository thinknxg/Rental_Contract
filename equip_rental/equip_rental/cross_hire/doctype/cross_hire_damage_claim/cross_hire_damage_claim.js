frappe.ui.form.on("Cross Hire Damage Claim", {
	refresh(frm) {
		if (frm.doc.docstatus === 1 && frm.doc.recoverable_from_customer
			&& frm.doc.status !== "Recovered") {
			frm.add_custom_button(__("Recover from Customer"), () => {
				frappe.prompt({ fieldname: "amount", label: __("Amount"),
					fieldtype: "Currency",
					default: frm.doc.accepted_amount || frm.doc.claimed_amount },
				(values) => {
					frm.call({ doc: frm.doc, method: "recover_from_customer",
						args: values }).then(() => frm.reload_doc());
				}, __("Recover Damage"), __("Add to Contract"));
			}).addClass("btn-primary");
		}
	},
});
