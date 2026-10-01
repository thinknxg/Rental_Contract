frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Return Note"), function() {
                frappe.model.open_mapped_doc({
                    method: "equip_rental.utils.sales_invoice_to_return.make_return_note",
                    frm: frm,
                });
            }, __("Create"));
        }
    },
});


// ---- JCR title rows: display-only (CSS class, survives grid redraws) ----
function is_title_row(d) {
    return d && d.jcr && !flt(d.amount) && !flt(d.contract_days) && !flt(d.excess_days);
}

function ensure_title_row_css() {
    if (document.getElementById("jcr-title-row-style")) return;
    $("<style id='jcr-title-row-style'>" +
        ".jcr-title-row .grid-static-col .static-area { visibility: hidden; }" +
        ".jcr-title-row .row-index span { visibility: hidden; }" +
        ".jcr-title-row .grid-static-col[data-fieldname='description'] .static-area { visibility: visible; font-weight: bold; }" +
        ".jcr-title-row .grid-static-col[data-fieldname='item_code'] .static-area { visibility: visible; font-size: 0; }" +
        ".jcr-title-row .grid-static-col[data-fieldname='item_code'] .static-area::after { content: '*'; font-size: 13px; font-weight: bold; }" +
        ".jcr-title-row .grid-static-col .field-area { visibility: hidden; }" +
        ".jcr-title-row .grid-static-col[data-fieldname='description'] .field-area { visibility: visible; }" +
        "</style>").appendTo("head");
}

function style_title_rows(frm) {
    const field = frm.fields_dict.items;
    if (!field || !field.grid) return;
    ensure_title_row_css();

    let n = 0;
    (field.grid.grid_rows || []).forEach((gr) => {
        const title = is_title_row(gr.doc);
        $(gr.wrapper).toggleClass("jcr-title-row", !!title);
        if (!title) {
            n += 1;
            const el = $(gr.wrapper).find(".row-index span").first();
            if (el.length && el.text() !== String(n)) el.text(n);
        }
    });
}

frappe.ui.form.on("Sales Invoice", {
    refresh(frm) {
        style_title_rows(frm);
        const wrapper = frm.fields_dict.items && frm.fields_dict.items.grid.wrapper;
        if (wrapper && !frm._title_rows_observer) {
            frm._title_rows_observer = new MutationObserver(() => {
                if (frm._title_rows_pending) return;
                frm._title_rows_pending = true;
                requestAnimationFrame(() => {
                    frm._title_rows_pending = false;
                    style_title_rows(frm);
                });
            });
            frm._title_rows_observer.observe(wrapper[0], { childList: true, subtree: true });
        }
    },
});


