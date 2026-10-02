"""Bridge between cross hire documents and ERPNext's procurement and stock cycle.

Cross-hired equipment is physically in our custody but financially never ours.
ERPNext models that exactly: a stock item received at **zero valuation rate**.
The Stock Ledger records the quantity so we always know which yard or site the
machine is in, while the General Ledger stays untouched because we own nothing.

    Cross Hire Order        -> Purchase Order    (commitment: custody + hire charges)
    Cross Hire Receipt      -> Purchase Receipt  (qty in, rate 0, no GL impact)
    Cross Hire Off Hire     -> Purchase Return   (qty out, rate 0, no GL impact)
    Invoice Reconciliation  -> Purchase Invoice  (the money, against the hire item)

The Purchase Order carries two kinds of line:

* **custody lines** - the stock item, qty 1, rate 0. Received and returned.
* **hire charge lines** - a non-stock service item at the vendor's rate. Invoiced.

Zero-amount custody lines do not distort `per_billed` (ERPNext bills on amount),
so the Purchase Order still completes correctly once the hire charges are paid.
"""

from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, getdate

from equip_rental.utils.common import get_settings


# ------------------------------------------------------------------ masters
def get_hire_charge_item():
    settings = get_settings()
    item = settings.cross_hire_item
    if not item:
        frappe.throw(_("Set a Default Hire Charge Item in Equipment Rental Settings"))
    return item


def ensure_stock_item(equipment_category):
    """The stock item representing hired-in units of a category.

    Hired-in kit must never share an item with owned kit: owned machines are
    fixed assets, hired ones are somebody else's asset sitting in our yard.
    """
    existing = frappe.db.get_value("Equipment Category", equipment_category,
                                   "cross_hire_item")
    if existing and frappe.db.exists("Item", existing):
        return existing

    settings = get_settings()
    item_code = "CH-{0}".format(frappe.scrub(equipment_category).upper()[:36])

    if not frappe.db.exists("Item", item_code):
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = "{0} (hired in)".format(equipment_category)[:140]
        item.item_group = (settings.cross_hire_item_group
                           or frappe.db.get_value("Item Group",
                                                  {"is_group": 0}, "name"))
        item.stock_uom = "Nos"
        item.is_stock_item = 1
        item.is_purchase_item = 1
        item.is_sales_item = 0
        item.is_fixed_asset = 0
        item.include_item_in_manufacturing = 0
        item.has_serial_no = cint(settings.track_cross_hire_serial_no)
        if item.has_serial_no:
            item.serial_no_series = "{0}-.#####".format(item_code)
        item.is_rental_item = 1
        item.is_cross_hire_item = 1
        item.description = _(
            "Equipment hired in from a vendor. Carried at zero valuation - "
            "quantity is tracked for custody, never for inventory value.")
        item.flags.ignore_permissions = True
        item.insert()

    frappe.db.set_value("Equipment Category", equipment_category, "cross_hire_item",
                        item_code, update_modified=False)
    return item_code


def get_yard_warehouse(company, order=None):
    settings = get_settings()
    warehouse = (order and order.set_warehouse) or settings.cross_hire_warehouse
    if warehouse and frappe.db.get_value("Warehouse", warehouse, "company") == company:
        return warehouse
    if warehouse:
        frappe.throw(_("Warehouse {0} does not belong to {1}").format(warehouse,
                                                                      company))
    frappe.throw(_("Set a Cross Hire Yard Warehouse in Equipment Rental Settings"))


def get_site_warehouse(company):
    settings = get_settings()
    return settings.cross_hire_site_warehouse or settings.cross_hire_warehouse


def is_stock_tracked(equipment):
    """Only cross-hired units are stock tracked; owned kit stays on the asset side."""
    if not equipment:
        return False
    row = frappe.db.get_value("Rental Equipment", equipment,
                              ["ownership", "stock_item"], as_dict=True)
    return bool(row and row.ownership == "Cross-Hired" and row.stock_item)


# ------------------------------------------------------------------ serial no
def serial_fields(row, item_code, serial_no):
    """ERPNext v15+ moved serial handling to Serial and Batch Bundle, but still
    accepts plain serial numbers when `use_serial_batch_fields` is set."""
    if not serial_no:
        return {}
    if not cint(frappe.db.get_value("Item", item_code, "has_serial_no")):
        return {}
    return {"use_serial_batch_fields": 1, "serial_no": serial_no}


def resolve_serial_no(receipt_row, item_code, fallback):
    settings = get_settings()
    if not cint(settings.track_cross_hire_serial_no):
        return None
    if not cint(frappe.db.get_value("Item", item_code, "has_serial_no")):
        return None
    serial = (receipt_row.get("serial_no") or receipt_row.get("vendor_plant_no")
              or fallback)
    if not serial:
        return None
    serial = str(serial).strip().replace(" ", "-")[:140]
    if frappe.db.exists("Serial No", serial):
        status = frappe.db.get_value("Serial No", serial, "status")
        if status == "Active":
            frappe.throw(
                _("Serial No {0} is already in stock. The vendor plant number must "
                  "be unique while the unit is on hire.").format(serial))
    return serial


# ------------------------------------------------------------------ purchase order
def make_purchase_order(order):
    """Raise the ERPNext Purchase Order behind a submitted Cross Hire Order."""
    settings = get_settings()
    warehouse = get_yard_warehouse(order.company, order)
    hire_item = get_hire_charge_item()

    po = frappe.new_doc("Purchase Order")
    po.supplier = order.supplier
    po.company = order.company
    po.currency = order.currency
    po.transaction_date = getdate(order.order_date)
    po.schedule_date = getdate(order.from_date)
    po.project = order.project
    po.cost_center = order.cost_center
    po.cross_hire_order = order.name

    # position of each appended row, so the mapping never has to be guessed back
    layout = []

    for item in order.items:
        if item.item_status == "Cancelled":
            continue
        item_code = item.item_code or ensure_stock_item(item.equipment_category)
        hire_code = item.hire_item or hire_item
        schedule = getdate(item.expected_from_date or order.from_date)

        custody_at = len(po.items)
        custody = po.append("items", {})
        custody.item_code = item_code
        custody.qty = flt(item.qty) or 1
        custody.rate = 0
        custody.warehouse = item.warehouse or warehouse
        custody.schedule_date = schedule
        custody.description = _("Custody of {0}{1} - hired in, zero valuation").format(
            item.description or item.equipment_category,
            " ({0})".format(item.vendor_plant_no) if item.vendor_plant_no else "")

        charge_at = len(po.items)
        charge = po.append("items", {})
        charge.item_code = hire_code
        charge.qty = flt(item.expected_units or 1) * (flt(item.qty) or 1)
        charge.rate = flt(item.rate)
        charge.schedule_date = schedule
        charge.cost_center = order.cost_center
        charge.project = order.project
        if settings.default_cross_hire_expense_account:
            charge.expense_account = settings.default_cross_hire_expense_account
        charge.description = _("{0} hire of {1} at {2} per {3}").format(
            item.rate_basis, item.description or item.equipment_category,
            flt(item.rate), item.rate_basis.lower())

        transport = flt(item.transport_in) + flt(item.transport_out)
        if transport:
            freight = po.append("items", {})
            freight.item_code = hire_code
            freight.qty = 1
            freight.rate = transport
            freight.schedule_date = schedule
            freight.cost_center = order.cost_center
            freight.project = order.project
            if settings.default_cross_hire_expense_account:
                freight.expense_account = settings.default_cross_hire_expense_account
            freight.description = _("Transport in/out for {0}").format(
                item.description or item.equipment_category)

        layout.append((item, item_code, hire_code, custody_at, charge_at))

    if not po.items:
        return None

    po.flags.ignore_permissions = True
    po.set_missing_values()
    po.insert()
    po.submit()

    for item, item_code, hire_code, custody_at, charge_at in layout:
        custody_row = po.items[custody_at]
        charge_row = po.items[charge_at]
        item.db_set("item_code", item_code, update_modified=False)
        item.db_set("hire_item", hire_code, update_modified=False)
        item.db_set("purchase_order_item", custody_row.name, update_modified=False)
        item.db_set("po_hire_item", charge_row.name, update_modified=False)
        item.db_set("warehouse", custody_row.warehouse, update_modified=False)

    return po.name


def sync_po_hire_qty(order):
    """An extended hire costs more units than the PO committed to. Bump the hire
    charge rows so the Purchase Invoice does not trip over-billing."""
    if not order.purchase_order:
        return
    if frappe.db.get_value("Purchase Order", order.purchase_order,
                           "docstatus") != 1:
        return

    po = frappe.get_doc("Purchase Order", order.purchase_order)
    mapped = {i.po_hire_item: i for i in order.items if i.po_hire_item}
    if not mapped:
        return

    changes = []
    resized = False
    for row in po.items:
        qty, rate = flt(row.qty), flt(row.rate)
        item = mapped.get(row.name)
        if item:
            required = flt(item.expected_units or 1) * (flt(item.qty) or 1)
            if required > qty:
                qty, resized = required, True
            rate = flt(item.rate)
        changes.append({"docname": row.name, "item_code": row.item_code,
                        "qty": qty, "rate": rate, "idx": row.idx})

    if not resized:
        return

    try:
        from erpnext.controllers.accounts_controller import update_child_qty_rate
        update_child_qty_rate("Purchase Order", frappe.as_json(changes), po.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(),
                         "Cross hire: could not resize PO {0}".format(po.name))
        frappe.msgprint(
            _("The hire was extended but Purchase Order {0} could not be resized. "
              "Update its quantities manually or the vendor invoice may be blocked.")
            .format(po.name), indicator="orange")


def close_purchase_order(order):
    settings = get_settings()
    if not (settings.close_po_on_off_hire and order.purchase_order):
        return
    if frappe.db.get_value("Purchase Order", order.purchase_order,
                           "docstatus") != 1:
        return
    po = frappe.get_doc("Purchase Order", order.purchase_order)
    if po.status not in ("Closed", "Completed"):
        po.update_status("Closed")


# ------------------------------------------------------------------ receipt
def make_purchase_receipt(receipt, order, rows):
    """Receive hired-in equipment: quantity only, rate zero, no GL impact.

    `rows` is a list of (receipt_row, order_item, serial_no).
    """
    warehouse = receipt.location or get_yard_warehouse(order.company, order)

    pr = frappe.new_doc("Purchase Receipt")
    pr.supplier = order.supplier
    pr.company = order.company
    pr.currency = order.currency
    pr.conversion_rate = 1
    pr.set_posting_time = 1
    posting = get_datetime(receipt.receipt_datetime)
    pr.posting_date = posting.date()
    pr.posting_time = posting.strftime("%H:%M:%S")
    pr.project = order.project
    pr.cost_center = order.cost_center
    pr.cross_hire_order = order.name
    pr.cross_hire_receipt = receipt.name
    pr.supplier_delivery_note = receipt.vendor_delivery_note

    for receipt_row, item, serial_no in rows:
        if serial_no and (flt(item.qty) or 1) != 1:
            frappe.throw(_("Row for {0}: a serial-tracked hire line must have quantity 1. "
                           "Add one line per machine.").format(item.equipment_category))
        line = pr.append("items", {})
        line.item_code = item.item_code
        line.qty = flt(item.qty) or 1
        line.received_qty = flt(item.qty) or 1
        line.rate = 0
        line.allow_zero_valuation_rate = 1
        line.warehouse = item.warehouse or warehouse
        line.cost_center = order.cost_center
        line.project = order.project
        if item.purchase_order_item:
            line.purchase_order = order.purchase_order
            line.purchase_order_item = item.purchase_order_item
        line.description = _("{0} hired in from {1} on {2}").format(
            receipt_row.description or item.description or item.equipment_category,
            order.supplier, pr.posting_date)
        line.update(serial_fields(line, item.item_code, serial_no))

    if not pr.items:
        return None

    pr.flags.ignore_permissions = True
    pr.set_missing_values()
    pr.insert()
    pr.submit()

    for index, (_row, item, _serial) in enumerate(rows):
        if index < len(pr.items):
            item.db_set("purchase_receipt_item", pr.items[index].name,
                        update_modified=False)
            item.db_set("received_qty", flt(pr.items[index].qty),
                        update_modified=False)
    return pr.name


# ------------------------------------------------------------------ return
def make_purchase_return(note, order, rows):
    """Send hired-in equipment back: a Purchase Receipt with is_return, negative
    quantity, rate zero. Stock leaves our books; no credit note is implied,
    because we never carried the value in the first place.

    `rows` is a list of (off_hire_row, order_item).
    """
    by_receipt = {}
    for off_row, item in rows:
        if not item.purchase_receipt_item:
            continue
        parent = frappe.db.get_value("Purchase Receipt Item",
                                     item.purchase_receipt_item, "parent")
        if not parent:
            continue
        by_receipt.setdefault(parent, []).append((off_row, item))

    if not by_receipt:
        return None

    created = []
    posting = get_datetime(note.actual_off_hire_date or note.notice_date)

    for source_name, group in by_receipt.items():
        source = frappe.get_doc("Purchase Receipt", source_name)
        received_at = get_datetime("{0} {1}".format(source.posting_date, source.posting_time))
        posting = max(posting, received_at + timedelta(minutes=1))

        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = order.supplier
        pr.company = order.company
        pr.currency = order.currency
        pr.conversion_rate = 1
        pr.is_return = 1
        pr.return_against = source.name
        pr.set_posting_time = 1
        pr.posting_date = posting.date()
        pr.posting_time = posting.strftime("%H:%M:%S")
        pr.project = order.project
        pr.cost_center = order.cost_center
        pr.cross_hire_order = order.name
        pr.cross_hire_off_hire_note = note.name

        for off_row, item in group:
            source_row = next((r for r in source.items
                               if r.name == item.purchase_receipt_item), None)
            if not source_row:
                continue
            returnable = flt(source_row.qty) - abs(flt(item.returned_qty))
            if returnable <= 0:
                continue

            line = pr.append("items", {})
            line.item_code = source_row.item_code
            line.qty = -1 * returnable
            line.received_qty = -1 * returnable
            line.rate = 0
            line.allow_zero_valuation_rate = 1
            line.warehouse = off_row.get("warehouse") or source_row.warehouse
            line.purchase_receipt_item = source_row.name
            line.cost_center = order.cost_center
            line.project = order.project
            line.description = _("Returned to {0} on {1} - off-hire ref {2}").format(
                order.supplier, pr.posting_date,
                note.vendor_off_hire_reference or note.name)
            line.update(serial_fields(line, source_row.item_code,
                                      item.serial_no or off_row.get("serial_no")))

        if not pr.items:
            continue

        pr.flags.ignore_permissions = True
        pr.set_missing_values()
        pr.insert()
        pr.submit()
        created.append(pr.name)

        for off_row, item in group:
            line = next((r for r in pr.items
                         if r.purchase_receipt_item == item.purchase_receipt_item),
                        None)
            if line:
                item.db_set("returned_qty",
                            flt(item.returned_qty) + abs(flt(line.qty)),
                            update_modified=False)

    return created[0] if created else None


def validate_in_stock(equipment, warehouse=None):
    """We cannot hand back to the vendor what is not physically in our yard."""
    settings = get_settings()
    if not cint(settings.block_offhire_without_stock):
        return
    row = frappe.db.get_value("Rental Equipment", equipment,
                              ["stock_item", "serial_no", "current_location"],
                              as_dict=True)
    if not (row and row.stock_item):
        return

    if row.serial_no:
        fields = ["status"]
        if frappe.get_meta("Serial No").has_field("warehouse"):
            fields.append("warehouse")
        sn = frappe.db.get_value("Serial No", row.serial_no, fields, as_dict=True) or {}
        status = sn.get("status")
        where = warehouse or row.current_location
        if where and sn.get("warehouse") and sn.get("warehouse") != where:
            frappe.throw(
                _("{0} (Serial No {1}) is in {2}, not {3}. Return it to the yard "
                  "before off-hiring it to the vendor.").format(
                    equipment, row.serial_no, sn.get("warehouse"), where))
        if status and status != "Active":
            frappe.throw(
                _("Serial No {0} for {1} is not in stock (status {2}). Bring the "
                  "unit back into the yard before off-hiring it to the vendor.")
                .format(row.serial_no, equipment, status))
        return

    warehouse = warehouse or row.current_location
    if not warehouse:
        return
    qty = frappe.db.get_value("Bin", {"item_code": row.stock_item,
                                      "warehouse": warehouse}, "actual_qty")
    if flt(qty) <= 0:
        frappe.throw(
            _("{0} shows no stock in {1}. Transfer the unit back to the yard "
              "before off-hiring it to the vendor.").format(equipment, warehouse))


# ------------------------------------------------------------------ transfers
def transfer_equipment(equipment, from_warehouse, to_warehouse, posting_datetime,
                       reference=None, remarks=None):
    """Material Transfer as a unit moves between the yard and a customer site."""
    settings = get_settings()
    if not cint(settings.transfer_stock_on_dispatch):
        return None
    if not is_stock_tracked(equipment):
        return None
    if not (from_warehouse and to_warehouse) or from_warehouse == to_warehouse:
        return None

    row = frappe.db.get_value("Rental Equipment", equipment,
                              ["stock_item", "serial_no", "company"], as_dict=True)
    qty = frappe.db.get_value("Bin", {"item_code": row.stock_item,
                                      "warehouse": from_warehouse}, "actual_qty")
    if flt(qty) <= 0:
        frappe.msgprint(
            _("{0} is not in stock at {1}, so no transfer was posted.").format(
                equipment, from_warehouse), indicator="orange", alert=True)
        return None

    entry = frappe.new_doc("Stock Entry")
    entry.stock_entry_type = "Material Transfer"
    entry.purpose = "Material Transfer"
    entry.company = row.company
    entry.set_posting_time = 1
    posting = get_datetime(posting_datetime)
    entry.posting_date = posting.date()
    entry.posting_time = posting.strftime("%H:%M:%S")
    entry.remarks = remarks

    line = entry.append("items", {})
    line.item_code = row.stock_item
    line.qty = 1
    line.s_warehouse = from_warehouse
    line.t_warehouse = to_warehouse
    line.allow_zero_valuation_rate = 1
    line.basic_rate = 0
    line.update(serial_fields(line, row.stock_item, row.serial_no))

    try:
        entry.flags.ignore_permissions = True
        entry.set_missing_values()
        entry.insert()
        entry.submit()
    except Exception:
        frappe.log_error(frappe.get_traceback(),
                         "Cross hire transfer failed: {0}".format(equipment))
        frappe.msgprint(
            _("Stock transfer for {0} could not be posted. Move it manually.")
            .format(equipment), indicator="orange")
        return None

    frappe.db.set_value("Rental Equipment", equipment, "current_location",
                        to_warehouse, update_modified=False)
    return entry.name


def on_dispatch(dispatch_doc):
    site = get_site_warehouse(dispatch_doc.company)
    for row in dispatch_doc.items:
        if not is_stock_tracked(row.equipment):
            continue
        source = frappe.db.get_value("Rental Equipment", row.equipment,
                                     "current_location")
        transfer_equipment(row.equipment, source, site,
                           dispatch_doc.dispatch_datetime,
                           remarks=_("Dispatched on {0}").format(dispatch_doc.name))


def on_return(return_doc):
    for row in return_doc.items:
        if not is_stock_tracked(row.equipment):
            continue
        order = frappe.db.get_value("Rental Equipment", row.equipment,
                                    "cross_hire_order")
        yard = (frappe.db.get_value("Cross Hire Order", order, "set_warehouse")
                if order else None) or get_settings().cross_hire_warehouse
        source = frappe.db.get_value("Rental Equipment", row.equipment,
                                     "current_location")
        transfer_equipment(row.equipment, source, yard, return_doc.return_datetime,
                           remarks=_("Returned on {0}").format(return_doc.name))
