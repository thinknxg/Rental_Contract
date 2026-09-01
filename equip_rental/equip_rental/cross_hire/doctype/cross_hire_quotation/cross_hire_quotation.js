frappe.ui.form.on("Cross Hire Quotation", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (frm.doc.cross_hire_requisition) {
			frm.add_custom_button(__("Compare Vendors"), () => {
				frappe.call({
					method: "equip_rental.cross_hire.doctype.cross_hire_quotation.cross_hire_quotation.compare",
					args: { cross_hire_requisition: frm.doc.cross_hire_requisition },
				}).then((r) => {
					const rows = (r.message || []).map((x) =>
						`<tr><td>${x.supplier}</td><td>${x.equipment_category}</td>
						<td>${x.description || ""}</td><td>${x.rate_basis}</td>
						<td class="text-right">${format_currency(x.rate)}</td>
						<td class="text-right">${format_currency(
							(x.transport_in || 0) + (x.transport_out || 0))}</td></tr>`).join("");
					frappe.msgprint({
						title: __("Vendor Comparison"), wide: true,
						message: `<table class="table table-bordered"><thead><tr>
							<th>${__("Vendor")}</th><th>${__("Category")}</th>
							<th>${__("Offer")}</th><th>${__("Basis")}</th>
							<th class="text-right">${__("Rate")}</th>
							<th class="text-right">${__("Transport")}</th>
							</tr></thead><tbody>${rows}</tbody></table>`,
					});
				});
			});
		}

		if (frm.doc.status !== "Awarded") {
			frm.add_custom_button(__("Award & Create Order"), () => {
				if (!(frm.doc.items || []).some((r) => r.is_selected)) {
					frappe.msgprint(__("Tick Award on the lines you are accepting"));
					return;
				}
				frappe.model.open_mapped_doc({
					method: "equip_rental.cross_hire.doctype.cross_hire_quotation.cross_hire_quotation.make_cross_hire_order",
					frm: frm,
				});
			}).addClass("btn-primary");
		}
	},
});
