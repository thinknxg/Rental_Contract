frappe.ui.form.on("Cross Hire Requisition", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Check Own Fleet First"), () => {
			frm.call({ doc: frm.doc, method: "check_own_fleet", freeze: true })
				.then((r) => {
					const rows = (r.message || []).map((x) =>
						`<tr><td>${x.category}</td><td>${x.own_fleet_available}</td>
						<td>${(x.equipment || []).join(", ") || "-"}</td></tr>`).join("");
					frappe.msgprint({
						title: __("Own Fleet Availability"),
						message: `<table class="table table-bordered"><thead><tr>
							<th>${__("Category")}</th><th>${__("Available")}</th>
							<th>${__("Units")}</th></tr></thead><tbody>${rows}</tbody></table>`,
					});
				});
		});

		if (["Draft", "Open", "Partially Ordered"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Cross Hire Order"), () => {
				frappe.model.open_mapped_doc({
					method: "equip_rental.cross_hire.doctype.cross_hire_requisition.cross_hire_requisition.make_cross_hire_order",
					frm: frm,
				});
			}, __("Create"));
		}
	},
});
