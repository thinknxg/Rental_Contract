frappe.query_reports["Equipment Utilization"] = {
	filters: [],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "utilization" && data) {
			const colour = data.utilization >= 70 ? "green"
				: (data.utilization >= 40 ? "orange" : "red");
			value = `<span style="color:var(--text-on-${colour}, inherit)">${value}</span>`;
		}
		return value;
	},
};
