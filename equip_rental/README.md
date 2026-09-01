# Equipment Rental (`equip_rental`)

A reusable Frappe v16 application for organisations that **use equipment internally
and rent equipment out to customers** from the same fleet. Built on ERPNext for
accounting, invoicing and item master.

## Highlights

- One equipment master serving internal usage and external hire
- Reservations -> Contract -> Dispatch -> Return -> Invoice lifecycle
- Availability engine that blocks double booking across contracts, reservations
  and maintenance downtime
- Rate cards by customer / category with hour, day, week and month bases
- Periodic billing (daily / weekly / monthly / on return) into ERPNext Sales Invoices
- Internal usage recharged to the using cost center via Journal Entry instead of
  being invoiced
- Sub-rental (hired-in) equipment with supplier orders and Purchase Invoices
- Three portals: public catalogue, customer portal, supplier portal
- Utilization, availability, revenue and overdue-return reports

## Install

```bash
bench get-app equip_rental /path/to/equip_rental
bench --site yoursite.local install-app equip_rental
bench --site yoursite.local migrate
bench build --app equip_rental
```

Requires `frappe` and `erpnext` (v15 or v16).

## First run

1. **Equipment Rental Settings** - company, price list, rental item group, billing
   defaults, portal switches and (if internal usage should hit the ledger) the
   internal recharge income / expense accounts.
2. **Equipment Category** - one per family of assets, with a default billing Item
   and maintenance intervals.
3. **Rental Rate Card** - hour/day/week/month rates, minimum billable units,
   deposits and delivery charges. Attach to a category, a unit, or a customer.
4. **Rental Equipment** - one record per physical unit. Tick *Published on Portal*
   to expose it in the public catalogue.

## Daily flow

| Step | Document | Effect |
|---|---|---|
| Enquiry | Rental Reservation | Soft-holds units, checks availability |
| Agreement | Rental Contract (submit) | Reserves units, sets the billing schedule |
| Handover | Rental Dispatch Note (submit) | Units go *On Rent* / *Internal Use*, meter-out captured |
| Collection | Rental Return Note (submit) | Off-rents lines, captures damage/fuel/cleaning charges, raises maintenance |
| Money | Rental Billing Run or contract *Bill Period* | Draft Sales Invoices, or Journal Entries for internal usage |

Nightly scheduler jobs advance contract status, expire stale reservations, warn
about returns due and document expiry, and run automatic billing for contracts
whose next billing date has arrived.

## Billing rules

- Hour and Day bases charge whole units (a part day is a full day).
- Week and Month bases are pro-rated, with monthly periods aligned to calendar
  months when *Bill Calendar Months* is enabled.
- `min_billable_units` on the rate card enforces a floor per line.
- Each line tracks `last_billed_upto`, so re-running a period never double bills.
- Additional charges (delivery, damage, fuel, cleaning, operator) are invoiced once
  and then flagged.

## Portal routes

| Route | Audience | Contents |
|---|---|---|
| `/rentals` | Public | Catalogue with category, text and date-availability filters |
| `/equipment/<slug>` | Public | Unit detail, specs, rates, booking request form |
| `/my-rentals` | Customer | Contracts, on-hire lines, invoices, off-hire requests |
| `/supplier-rentals` | Supplier | Sub-rental orders and units on hire to you |

## Whitelisted API

```
equip_rental.api.catalogue(equipment_category, from_date, to_date, search)
equip_rental.api.check_availability(equipment, from_date, to_date)
equip_rental.api.quote(equipment, from_date, to_date, rate_basis, qty)
equip_rental.api.request_booking(...)
equip_rental.api.my_contracts(status)
equip_rental.api.request_off_hire(rental_contract, requested_date, equipment)
equip_rental.api.supplier_orders()
equip_rental.utils.availability.get_available_equipment(...)
equip_rental.utils.billing.create_invoice_for_contract(contract, period_from, period_to)
```

## Roles

- **Rental Manager** - full control including submit/cancel
- **Rental User** - day to day operations
- **Customer / Supplier** - portal only, scoped by contact links

## Custom fields added to ERPNext

`Sales Invoice.rental_contract`, `Sales Invoice.rental_period_from/to`,
`Sales Invoice Item.rental_equipment`, `Purchase Invoice.sub_rental_order`,
`Item.is_rental_item`, `Customer.default_rate_card`, `Supplier.is_rental_supplier`.

MIT licensed.
