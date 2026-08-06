frappe.ui.form.on("Rental Equipment", {
	refresh(frm) {
		if (frm.doc.__islocal) return;

		frm.add_custom_button(__("Availability"), () => {
			frappe.set_route("query-report", "Equipment Availability",
				{ equipment: frm.doc.name });
		}, __("View"));

		frm.add_custom_button(__("Maintenance Log"), () => {
			frappe.new_doc("Rental Maintenance Log", { equipment: frm.doc.name });
		}, __("Create"));

		frm.add_custom_button(__("Meter Reading"), () => {
			frappe.new_doc("Rental Meter Reading", { equipment: frm.doc.name });
		}, __("Create"));

		if (frm.doc.published && frm.doc.route) {
			frm.add_custom_button(__("View on Website"), () => {
				window.open("/" + frm.doc.route);
			});
		}

		const colour = {
			"Available": "green", "Reserved": "orange", "On Rent": "blue",
			"Internal Use": "purple", "In Maintenance": "yellow",
			"Out of Service": "red", "Retired": "grey",
		}[frm.doc.status] || "grey";
		frm.dashboard.set_headline_alert(
			`<span class="indicator ${colour}">${__(frm.doc.status)}</span>`);
	},
});
