frappe.ui.form.on("Cross Hire Off Hire Note", {
	cross_hire_order(frm) {
		if (!frm.doc.cross_hire_order) return;
		frappe.db.get_value("Cross Hire Order", frm.doc.cross_hire_order,
			"off_hire_notice_days").then((r) => {
			const days = (r.message || {}).off_hire_notice_days;
			if (days && !frm.doc.requested_collection_date) {
				frm.set_value("requested_collection_date",
					frappe.datetime.add_days(frappe.datetime.get_today(), days));
			}
		});
	},
});
