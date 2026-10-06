# 017 — Seller Plans, Subscriptions, and Commission

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §10](../../../README.md#10-seller-plans-subscriptions-and-commission). API contract: [`docs/api/seller_plans.md`](../api/seller_plans.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

(README build-order step 6. It was not in the original numbered feature list, so it took the next free number.)

## Purpose

Decide what MUHUZE charges a seller on each sale. A seller either has a **plan** (a subscription fee in exchange for a lower commission) or is on the **default commission rate**. Orders, the next money feature, will ask this feature one question and store the answer:

> What commission rate applies to this seller right now?

## The answer, in one place

`SellerPlanService.resolve_commercial_terms(seller_id, at)`:

```
a subscription in force at that moment  →  its commission rate   (may be 0%)
otherwise                               →  the default rate in force at that moment
neither                                 →  refuse: "MUHUZE has not set its commission rate yet"
```

**Nothing else in the codebase may compute a commission rate.** The call is read-only, so orders can make it inside their own transaction, and it returns where the rate came from (which subscription and plan, or which default-rate row) for the order to record.

## Rules

**Decided 2026-10-07** (README §20 `C3`, `C5`–`C7`, `C9`–`C12`):

1. **Each plan has its own length in days**, set by the admin.
2. **A subscription keeps the price and commission rate it was requested with.** Editing a plan affects only later requests.
3. **No automatic renewal.** The seller requests again.
4. **No grace period.** When a subscription ends, the default rate applies from that moment. A seller is never blocked from selling for lack of a plan.
5. **Getting a plan, until online payment exists:** the seller requests one, pays MUHUZE outside the app, and an admin activates it after checking the payment. An admin can also assign a plan directly.
6. **Renewing the same plan early adds on:** the new period starts when the current one ends. **Switching to a different plan takes effect at once**, ending the current one with no refund.
7. **There is no "standard" plan.** No subscription means the default rate.
8. **Subscriptions cannot be paid from the wallet.**
9. **The default rate has no built-in value.** Until an admin sets one, a seller without a plan has no rate, and orders cannot be created for them.

**Plans**

- Plans are data. **No plan name, price, or rate is written in code**, and none is seeded.
- A plan has a stable `code` (never changed), a name, a price in RWF (0 is allowed), a length in days, and a commission rate from 0 to 100.
- A **retired** plan cannot be requested or assigned. Subscriptions to it run their course.
- A plan any subscription has used cannot be deleted, only retired.
- Anyone can see the plans on offer. Only staff see retired ones.

**Subscriptions**

```
        request                      activate
seller ─────────► PENDING ─────────────────────────► ACTIVE ──(time passes)──► no longer applies
                    │  reject / withdraw                │ cancel / replaced
                    ▼                                   ▼
            REJECTED / CANCELLED                    CANCELLED
```

- A seller has a **history** of subscriptions, never one editable field. Nothing is deleted.
- **Applicable** at a moment = status `active` **and** `starts_at ≤ moment < ends_at`. "Expired" is not a status: an active subscription simply stops applying when its end passes. No background job is involved.
- **At most one subscription per seller applies at any moment.** PostgreSQL enforces this with an exclusion constraint on the periods of active subscriptions; it does not depend on the application getting it right.
- One open request per seller (also enforced by the database). The seller can withdraw it.
- Rejecting and cancelling need a reason, which the seller sees.
- Cancelling a running subscription ends it now. Cancelling a scheduled one (not started yet) just stops it from starting.
- Requesting needs an **active** seller. A suspended seller's existing subscription keeps running.

**The default commission rate**

- **Effective-dated and append-only.** Changing it adds a row with the moment it takes effect; nothing is edited. There is always a record of who set which rate, when, and why.
- A rate can take effect now or be scheduled for a future moment. It cannot be backdated.
- Changing it never affects an order already created: the order will have recorded its own rate.

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `seller_plan.manage` | Create, change, retire, delete plans; see retired ones | – |
| `seller_subscription.manage` | See every subscription; activate, reject, assign, cancel | – |
| `default_commission_rate.manage` | See and change the default rate and its history | – |
| `seller_subscription.request` | Request a plan for your own shop; see your own subscriptions | `seller` |

The three staff permissions change what MUHUZE earns, so each is separate (README §5.4). Only `admin` holds them until assigned.

## Design

```
app/modules/seller_plans/
├── seller_plan_routes.py        # /seller-plans, /seller-subscriptions, /commission-rates/default
├── seller_plan_dependencies.py
├── seller_plan_service.py       # resolve_commercial_terms; scheduling; every rule above
├── seller_plan_repository.py
├── seller_plan_model.py         # SellerPlan, SellerSubscription, DefaultCommissionRate
├── seller_plan_schema.py
├── seller_plan_permissions.py
├── seller_plan_exceptions.py
└── seller_plan_constants.py
```

**Scheduling a subscription** (`_schedule`), when one is activated or assigned:

| The seller's running or scheduled subscriptions | The new one |
|---|---|
| None | Starts now |
| The latest is the **same plan** | Starts when that one ends |
| A **different plan** | Those are ended now ("Replaced by a new plan"); the new one starts now |

The seller's unfinished subscriptions are locked while this runs. If two changes still collide, the exclusion constraint refuses the second and the caller gets `409`.

**Database.** Migration `0006` installs the `btree_gist` extension (shipped with PostgreSQL) for the exclusion constraint.

**Money and rates** are `NUMERIC` and `Decimal` end to end, and are returned as strings (`"10000.00"`, `"7.50"`).

## What this feature does not do

| Not done | Why | Planned with |
|---|---|---|
| Take payment for a subscription | No payments feature yet. An admin confirms a payment made outside the app and records its reference | `011_payments`: activation will follow a confirmed payment |
| Record subscription revenue | Revenue accounting is a separate feature. The subscription holds the price owed | Revenue accounting (README §13) |
| Tell the seller when a plan is about to end, or was activated or rejected | No notifications yet | `014_notifications` |
| Refund or prorate on a switch or cancellation | Decided: none (`C9`) | – |

## Security review

- [x] Every staff endpoint needs its specific permission; a seller gets `403` on all 14, including for their own subscription.
- [x] A seller can request and withdraw only their own subscriptions; another seller's is `404`.
- [x] A seller cannot activate their own request.
- [x] Rates are bounded 0 to 100 by the schema and by database checks; money cannot be negative.
- [x] The default rate cannot be backdated, so past sales cannot be re-explained.
- [x] Every plan, subscription, and rate change records the acting account and is logged.
- [x] One applicable subscription per seller is guaranteed by the database.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| Activation relies on an admin having really checked the payment | A plan could be activated without payment | `011_payments` |
| A cancelled subscription in the middle of a queue leaves a gap on the default rate | Surprising, but correct by the rules | Revisit if renewals become common |
| No list of sellers whose plan ends soon | Staff can't chase renewals | `016_reporting` |
| A free plan (`price` 0) still needs an admin to activate each request | Extra work | Auto-activate free plans, if wanted |

## Progress

- [x] Requirements and rules (this document, README §10, decisions `C3`, `C5`–`C7`, `C9`–`C12`)
- [x] Database design and migration `0006` (applied to the development database)
- [x] Models, repository, service, schemas, routes, permissions
- [x] The commission resolver for orders
- [x] Tests written: `tests/api/seller_plans/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [ ] **An admin sets the real default commission rate and creates the real plans** (README §20 `C1`, `C2`, `C4`: business values, entered as data)
