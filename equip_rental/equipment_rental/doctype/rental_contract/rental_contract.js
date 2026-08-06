frappe.ui.form.on("Rental Contract", {
	setup(frm) {
		frm.set_query("equipment", "items", () => ({
			filters: { status: ["not in", ["Retired", "Out of Service"]],
				company: frm.doc.company },
		}));
	},

	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		if (!["Closed", "Cancelled"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Dispatch Note"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.equipment_rental.doctype.rental_contract.rental_contract.make_dispatch_note",
					frm: frm,
				});
			}, __("Create"));

			frm.add_custom_button(__("Return Note"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.equipment_rental.doctype.rental_contract.rental_contract.make_return_note",
					frm: frm,
				});
			}, __("Create"));

			if (frm.doc.contract_type === "Customer Rental") {
				frm.add_custom_button(__("Sales Invoice"), () => {
					frappe.prompt([
						{ fieldname: "period_from", label: __("Period From"),
							fieldtype: "Date", reqd: 1,
							default: frm.doc.next_billing_date || frm.doc.start_date },
						{ fieldname: "period_to", label: __("Period To"),
							fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
					], (values) => {
						frm.call({ doc: frm.doc, method: "bill_now", args: values,
							freeze: true }).then((r) => {
							if (r.message) {
								frappe.set_route("Form", "Sales Invoice", r.message);
							} else {
								frappe.msgprint(__("Nothing to bill for this period"));
							}
						});
					}, __("Bill Period"), __("Create Invoice"));
				}, __("Create"));
			}

			frm.add_custom_button(__("Extend"), () => {
				frappe.prompt({ fieldname: "new_end_date", label: __("New End Date"),
					fieldtype: "Date", reqd: 1 }, (values) => {
					frm.call({ doc: frm.doc, method: "extend_contract", args: values })
						.then(() => frm.reload_doc());
				}, __("Extend Contract"), __("Extend"));
			});

			frm.add_custom_button(__("Close"), () => {
				frappe.confirm(__("Close this contract?"), () => {
					frm.call({ doc: frm.doc, method: "close_contract" })
						.then(() => frm.reload_doc());
				});
			});
		}

		frm.add_custom_button(__("Invoices"), () => {
			frappe.set_route("List", "Sales Invoice",
				{ rental_contract: frm.doc.name });
		}, __("View"));
	},
});
