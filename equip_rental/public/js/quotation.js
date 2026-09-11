frappe.ui.form.on('Quotation', {
    party_name: function(frm) {
        if (frm.doc.quotation_to === 'Customer' && frm.doc.party_name) {
            frappe.db.get_value('Customer', frm.doc.party_name, 'tax_id', (r) => {
                if (r && r.tax_id) {
                    frm.set_value('customer_trn', r.tax_id);
                }
            });
        } else {
            frm.set_value('customer_trn', '');
        }
    },

    custom_deal_type: function(frm) {
        frm.fields_dict.items.grid.refresh();
    },
});
