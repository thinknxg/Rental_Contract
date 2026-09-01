frappe.ui.form.on("Cross Hire Order", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;

		if (!["Off Hired", "Closed", "Cancelled"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Cross Hire Receipt"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.cross_hire.doctype.cross_hire_order.cross_hire_order.make_cross_hire_receipt",
					frm: frm,
				});
			}, __("Create"));

			frm.add_custom_button(__("Off-Hire Note"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.cross_hire.doctype.cross_hire_order.cross_hire_order.make_off_hire_note",
					frm: frm,
				});
			}, __("Create"));

			frm.add_custom_button(__("Extend Hire"), () => {
				frappe.prompt([
					{ fieldname: "new_off_hire_date", label: __("New Off-Hire Date"),
						fieldtype: "Date", reqd: 1 },
					{ fieldname: "vendor_approval_reference",
						label: __("Vendor Approval Reference"), fieldtype: "Data" },
				], (values) => {
					frm.call({ doc: frm.doc, method: "extend_hire", args: values })
						.then(() => frm.reload_doc());
				}, __("Extend Vendor Hire"), __("Extend"));
			});
		}

		frm.add_custom_button(__("Invoice Reconciliation"), () => {
			frappe.new_doc("Cross Hire Invoice Reconciliation",
				{ cross_hire_order: frm.doc.name, company: frm.doc.company });
		}, __("Create"));

		frm.add_custom_button(__("Cost to Date"), () => {
			frm.call({ doc: frm.doc, method: "cost_to_date" }).then((r) => {
				const rows = (r.message || []).map((x) =>
					`<tr><td>${x.description}</td><td class="text-right">${x.units}</td>
					<td class="text-right">${format_currency(x.amount, frm.doc.currency)}</td>
					<td class="text-right">${format_currency(x.invoiced, frm.doc.currency)}</td>
					<td class="text-right">${format_currency(x.uninvoiced, frm.doc.currency)}</td>
					</tr>`).join("");
				frappe.msgprint({
					title: __("Accrued Hire Cost"), wide: true,
					message: `<table class="table table-bordered"><thead><tr>
						<th>${__("Line")}</th><th class="text-right">${__("Units")}</th>
						<th class="text-right">${__("Accrued")}</th>
						<th class="text-right">${__("Invoiced")}</th>
						<th class="text-right">${__("Uninvoiced")}</th>
						</tr></thead><tbody>${rows}</tbody></table>`,
				});
			});
		}, __("View"));

		if (frm.doc.rental_contract) {
			frm.add_custom_button(__("Re-Hire Contract"), () => {
				frappe.set_route("Form", "Rental Contract", frm.doc.rental_contract);
			}, __("View"));
		}
	},
});
