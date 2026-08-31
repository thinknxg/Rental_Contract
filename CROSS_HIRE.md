# Cross Hire Management

Cross hire (plant hire calls it *hired-in*, *re-hire* or *back-to-back hire*):
we do not own the machine. We hire it from a vendor, use it on our own project
or re-hire it to our customer, and give it back at the end of the hire.

The whole module exists to manage one uncomfortable fact: **two clocks run at
once, and they never quite line up.**

```
vendor clock   |----------------------------------------------|
               on-hire date                        off-hire date (their ref)
customer clock       |---------------------------|
                     dispatch                 return
                 ^^^^^                         ^^^^^^^^^^^^^^^^
              paid, not earning            paid, not earning  <- the leak
```

Every control below exists to squeeze those two gaps.

## Core design decision

A cross-hired unit becomes an **ordinary `Rental Equipment` record** the moment
it is received, with `ownership = Cross-Hired` and a *hire window*
(`hire_available_from` / `hire_available_upto`).

That means contracts, dispatch notes, returns, availability search, the portal
and customer invoicing all work on hired-in equipment with **no special cases**.
Cross Hire only adds the cost side and one hard constraint:

> A cross-hired unit can never be committed to a customer outside the window we
> hold it from the vendor.

Enforced in `utils/cross_hire.validate_hire_window()`, called from
`utils/availability.validate_availability()` - so it fires on contract save,
contract extension, reservation confirmation and portal availability search
alike. Extending the customer contract past the vendor date is blocked until the
Cross Hire Order is extended.

## Document flow

```
Rental Contract (customer needs a machine we do not have)
        |
        v
Cross Hire Requisition  --"Check Own Fleet First"--> maybe we do have one
        |
        v
Cross Hire Quotation (per vendor)  --compare--> award
        |
        v
Cross Hire Order  ------------------------------------ vendor commitment
        |   (submit)                                    notice period, terms,
        |                                               damage cap, fuel policy
        v
Cross Hire Receipt  --> creates Rental Equipment (Cross-Hired)
        |               vendor clock STARTS here, not at the order date
        v
   [ the unit now behaves like any owned machine ]
   Rental Contract -> Dispatch -> Return -> Sales Invoice
        |
        v
Cross Hire Off Hire Note --> vendor off-hire reference captured
        |                    vendor clock STOPS here; unit leaves the fleet
        v
Cross Hire Invoice Reconciliation --> Purchase Invoice
        |
        v
Cross Hire Damage Claim --> recover from customer contract where liable
```

## The six leak controls

| # | Leak | Control |
|---|---|---|
| 1 | Customer contract runs past the vendor return date | Hire-window validation blocks the contract; extend the order first |
| 2 | Machine sits on our yard idle while the vendor meter runs | `Idle Cross Hired Equipment` report + nightly alert with cash burnt |
| 3 | Notice period missed, vendor keeps charging | `alert_off_hire_notice_due` fires `notice_days` before the due date; the off-hire note warns on short notice |
| 4 | Customer returned it, nobody told the vendor | `alert_orphan_cross_hire` compares customer return against vendor off-hire status |
| 5 | Vendor bills past the off-hire date | `Cross Hire Invoice Reconciliation` rebuilds expected charges from our own dates and compares line by line; only approved amounts reach the Purchase Invoice |
| 6 | Vendor damage charge never recovered from the customer who caused it | `Cross Hire Damage Claim` -> pushes the charge onto the customer contract as a Damage Recovery line |

## Costing

`expected_cost()` reuses the same `get_billable_units()` engine as customer
billing, so vendor cost and customer revenue are computed on identical rules
(hour/day whole units, week/month pro-rated, minimum hire units enforced).

- **Accrual**: nightly job refreshes `accrued_amount` per line - incurred cost
  before the vendor invoice arrives.
- **Vendor invoicing**: only through reconciliation, which stamps
  `invoiced_upto` so the next period cannot be double paid.
- **Margin**: `Cross Hire Margin` report puts hire cost (plus transport and
  damage) against re-hire revenue pulled from `Sales Invoice Item.rental_equipment`.
- **Internal use**: the same unit issued to our own project carries cost to the
  project cost center via the Purchase Invoice, and shows on the margin report
  as cost with no revenue - which is the honest picture.

## Off-hire discipline

The vendor's off-hire reference number is the only evidence of when their
charges stopped. `require_vendor_offhire_reference` in Equipment Rental Settings
makes it mandatory before an off-hire date can be recorded, and the off-hire
note refuses to release a unit that is still on rent to a customer.

## DocTypes

Sourcing: Cross Hire Rate Agreement, Cross Hire Requisition, Cross Hire Quotation
Hire cycle: Cross Hire Order, Cross Hire Receipt, Cross Hire Off Hire Note
Cost control: Cross Hire Invoice Reconciliation, Cross Hire Damage Claim

## Reports

Cross Hire Register, Idle Cross Hired Equipment, Cross Hire Margin,
Cross Hire Vendor Variance.

## Migration from v1.0

`Sub Rental Order` is superseded. The patch
`equip_rental.patches.v1_1.migrate_sub_rental_to_cross_hire` converts existing
records into Cross Hire Orders, renames the `Sub-Rented` ownership value to
`Cross-Hired`, and drops the old doctypes.
