frappe.ui.form.on("Rental Return Note", {
refresh: function(frm) {
if (frm.doc.docstatus === 1) {
frm.add_custom_button(__("Sales Invoice"), function() {
frappe.call({
method: "equip_rental.equipment_rental.doctype.rental_return_note.rental_return_note.make_sales_invoice",
args: {
source_name: frm.doc.name
},
callback: function(r) {
if (r.message) {
frappe.model.sync(r.message);
frappe.set_route("Form", r.message.doctype, r.message.name);
}
}
});
}, __("Create"));
}
}
});
