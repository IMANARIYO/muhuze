# 011 — Payments (Phase 1: manual)

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §12](../../../README.md#12-payments-and-gateway-integration). API contract: [`docs/api/payments.md`](../api/payments.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Get the buyer's money to MUHUZE, and let MUHUZE record, reliably and exactly once, that it arrived. That record is what releases an order to its sellers.

**The buyer always pays MUHUZE, never a seller.** A seller is paid later, from their wallet, by withdrawal (README §2).

## How it works today

```
Buyer places an order
  │
  ▼
Buyer opens the payment instructions      MUHUZE's active receiving accounts
  │
  ▼
Buyer pays MUHUZE outside the app         mobile money, merchant code, or bank
  │
  ▼
Buyer submits the transaction reference   payment = awaiting_verification
  │
  ▼
Staff check MUHUZE's real statement
  │
  ├── approve ──► confirm_payment() ──► payment = paid ──► order released to its sellers
  └── reject (with a reason) ──► the buyer can submit again
```

This is **Phase 1**. There is no payment gateway, and none is needed to operate.

## The one confirmation path

`PaymentService.confirm_payment(payment_id, verified_by=…)` is the **only** way a payment becomes paid (README §12.1).

- A member of staff approving goes through it, with `verified_by` set to their account.
- A gateway (Phase 2) will call the same function after verifying its own confirmation, with `verified_by=None`.
- Everything after it (the order released, revenue recorded, sellers' wallets credited) is identical either way and never learns which it was.

It is **idempotent** (README §12.8). Confirming a payment that is already paid changes nothing and creates nothing twice, protected three ways:

1. the payment row is locked, and only `awaiting_verification → paid` does anything;
2. `OrderService.mark_paid` is itself idempotent;
3. the database allows only **one paid payment per order**.

Its whole effect is **one transaction**: if the order cannot be released (for example it was cancelled meanwhile), the payment is not marked paid either.

## Rules

**Decided 2026-10-07** (README §20 `D3`, `D5`–`D8`, `P2`):

1. **Several receiving accounts can be active at once**, with at most one default, shown first.
2. **The buyer submits** the account they paid, the transaction reference, and the phone number or name they paid from. **No screenshot is collected.**
3. **A transaction reference is used once**, whatever its letter case. The database refuses a second payment claiming it. A reference from a *rejected* attempt can be submitted again.
4. **A payment is always for the order's full total.** No part payments, and one order is never split across payments. The client cannot choose the amount.
5. **One member of staff approves**, with the `payment.verify` permission. There is no second approver. **Nobody can verify a payment they made themselves.**
6. **Approving marks the payment paid and releases the order in one step.**
7. **Rejecting needs a reason the buyer sees.** The buyer can submit again; every attempt is kept.
8. **Paying for a seller plan is not here yet.** Staff still activate a plan after checking its payment (feature 017); it moves into this table later.

**Receiving accounts**

- Managed by staff with `payment_destination.manage`. **No real number or name is written in code, seeded, or used in tests**: they are data.
- An account has a method (`mobile_money`, `merchant_code`, `bank_transfer`), a provider, the number or code to pay, the registered name the buyer should see, and optional instructions.
- An **inactive** account is never shown to buyers and cannot be the default. Deactivating the default leaves no default.
- An account that any payment has used cannot be deleted, only deactivated.
- **Buyers see them only for their own order while it awaits payment**, and only the fields needed to pay. There is no public list of MUHUZE's accounts (README §12.3).

**Snapshots.** A payment keeps a copy of the account it was made to and of the order number. If MUHUZE later changes or retires that account, the payment still shows where the money was actually sent.

**Statuses.** `awaiting_verification`, `paid`, `rejected`. Only what a real flow needs today; `pending`, `refunded`, and others join when a gateway or refunds are built (README §12.2).

**What staff check before approving** (against MUHUZE's actual statement, README §12.5): the reference, the amount, the date, the account it was sent to, and who sent it. The staff view shows all of these.

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `payment_destination.manage` | See and manage MUHUZE's receiving accounts | – |
| `payment.verify` | See every payment; approve and reject | – |

Each decides where money goes or whether it counts as received, so they are separate and only `admin` holds them until assigned. Paying for your own order needs only a login.

## Design

```
app/modules/payments/
├── payment_routes.py        # /orders/mine/{id}/payment, /payments, /payment-destinations
├── payment_dependencies.py
├── payment_service.py       # confirm_payment; submit; approve/reject; destinations
├── payment_repository.py
├── payment_model.py         # PaymentDestination, Payment
├── payment_schema.py
├── payment_permissions.py
├── payment_exceptions.py
└── payment_constants.py
```

**What payments ask orders:** `get_order_of_buyer` (the buyer's own order, or 404) and `mark_paid` (release it). Orders know nothing about payments.

**Guaranteed by the database:** one paid payment per order; one attempt awaiting verification per order; a reference used once among attempts that were not rejected; at most one default account per currency, and a default is always active.

**Ready for Phase 2.** `channel` (`manual` today) and `purpose` (`order` today) are columns, not assumptions. A gateway adds an adapter that verifies the provider's confirmation and calls `confirm_payment`; it adds a table for the provider's raw events at that point, not before.

## Security review

- [x] A payment becomes paid only through `confirm_payment`, after staff verification. A buyer's submission never pays anything (tested).
- [x] The amount comes from the order; a client-sent `amount` or `status` is ignored.
- [x] Staff endpoints need their specific permission; buyers and sellers get `403` on all 11.
- [x] MUHUZE's accounts are shown only to the buyer of an order awaiting payment.
- [x] Staff cannot approve or reject their own payment.
- [x] A reference cannot be reused, enforced by the database.
- [x] Approval is idempotent and auditable (who, when).
- [x] Account numbers and names are never written to logs; only ids.
- [x] No real account details exist anywhere in the repository.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| **No refunds** | A paid part that the seller rejects is taken back out of the seller's wallet ([012](012_wallets.md)), but the buyer must be refunded by hand, outside the system | README §20 `R1`–`R4` |
| A buyer can cancel an order while its payment awaits verification | If the money was really sent, staff must reject the payment and refund by hand | Block cancelling while a payment is waiting, or auto-reject; decide with refunds |
| Verification relies on staff reading the statement correctly | A wrong approval releases an unpaid order | A second approver (`D8`), or a gateway |
| No reconciliation report | Payments and the statement are matched one by one | README §12.9 |
| Subscriptions are not paid through here | Plan payments have no record beyond a reference | Move plan payments here (`purpose = subscription`) |
| The buyer is not told when a payment is approved or rejected | They must check the app | `014_notifications` |

## Progress

- [x] Requirements and rules (this document, README §12)
- [x] Database design and migration `0008` (applied to the development database)
- [x] Models, repository, service, schemas, routes, permissions
- [x] The single, idempotent `confirm_payment`
- [x] Tests written: `tests/api/payments/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [ ] **Staff enter MUHUZE's real receiving accounts** (README §20 `D1`, `D2`: business data)
