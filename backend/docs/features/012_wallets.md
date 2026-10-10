# 012 — Revenue and wallets

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §13](../../../README.md#13-revenue-accounting-and-seller-wallet), [§14](../../../README.md#14-financial-invariants). API contract: [`docs/api/wallets.md`](../api/wallets.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Record what happens to the buyer's money once MUHUZE has it: how much of each sale is MUHUZE's commission, and how much MUHUZE now owes the seller.

**A wallet is a debt MUHUZE holds, not money in the seller's hands.** Money reaches a seller only through a withdrawal (the next feature).

## How it works

```
Payment confirmed                       (feature 011)
  │   for each shop in the order:
  ├── revenue record                    the split: buyer paid / MUHUZE's commission / seller's share
  └── wallet movement  "earning"        + seller's share → PENDING
  │
Seller accepts and ships; the buyer confirms receipt
  └── wallet movement  "settlement"     pending → AVAILABLE   (can be withdrawn)

Seller rejects a part that was already paid
  └── wallet movement  "reversal"       − pending; the revenue record is marked reversed
```

All of this happens **inside the same transaction** as the step that caused it. A payment, the order's release, the revenue records, and the wallet credits succeed or fail together.

## Rules

**Decided 2026-10-07** (README §20 `W1`, `W2`, `W7`, `X4`):

1. **One wallet per seller, in RWF**, created with their first earning. It has two balances, **pending** and **available**, and two running totals, earned and withdrawn. A seller who has not sold yet is shown zeros.
2. **When a payment is confirmed, each seller's share goes to their pending balance** and MUHUZE's commission is recorded as revenue, in the same step. The amounts are the ones frozen on the seller order when it was placed; nothing is recalculated, so a later change of plan or default rate never alters them.
3. **A seller's share becomes available when the buyer confirms receipt of that seller's part.** There is no extra waiting period. Shipping is not enough. Each shop's part settles on its own.
4. **If a seller rejects a part that is already paid, their earning is taken back with a new reversing movement.** Nothing is deleted or edited. A reversed sale no longer counts as revenue. **Giving the buyer their money back is still done by hand**, outside the system.
5. **No request can set or add to a balance.** Every endpoint here is read-only.
6. **MUHUZE has no wallet of its own.** What MUHUZE earned is the total commission in the revenue records.
7. **Staff cannot make manual corrections yet.**

**The ledger.** A balance is never just a number. Every change writes a `wallet_transactions` row holding what moved and the balances afterwards, and the balances always equal the sum of those rows. One function, `WalletService._move`, is the only code that changes a balance.

**Exactly once.** Each of the three movements is safe to repeat:

| Movement | Called by | Repeated |
|---|---|---|
| `record_earning` | `OrderService.mark_paid` | does nothing |
| `settle` | `OrderService.confirm_receipt` | does nothing |
| `reverse` | the seller rejecting a paid part | does nothing |

and the database enforces it independently of the code: one revenue record per seller order, and one movement of each kind per revenue record.

**What makes no sense is refused:** releasing an earning that was reversed, reversing one that was already released, or moving an earning that was never recorded.

## Who sees what

| Who | Sees |
|---|---|
| Seller | Their own wallet and its movements. Also while suspended: it is what they are owed |
| Staff with `wallet.read` | Any seller's wallet and movements |
| Staff with `revenue.read` | Every revenue record, and totals (MUHUZE's commission income) |
| Buyer | Nothing here |

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `wallet.read_own` | See your own shop's wallet | `seller` |
| `wallet.read` | See any seller's wallet | – |
| `revenue.read` | See revenue records and totals | – |

## Design

```
app/modules/wallets/
├── wallet_routes.py         # /wallet/mine, /wallets/{seller_id}, /revenue  (all GET)
├── wallet_dependencies.py
├── wallet_service.py        # record_earning, settle, reverse; reading; reconcile
├── wallet_repository.py
├── wallet_model.py          # RevenueTransaction, Wallet, WalletTransaction
├── wallet_schema.py
├── wallet_permissions.py
├── wallet_exceptions.py
└── wallet_constants.py
```

**Who calls whom.** Orders call the wallet ledger; wallets know nothing about orders or payments beyond the ids they are given. The ledger methods do not commit: the caller's transaction owns them.

**Locking.** A movement locks the wallet row first, so two movements for one seller cannot read the same balance.

**Guaranteed by the database:** one revenue record per seller order; commission + seller share = the gross amount; one earning, one settlement, and at most one reversal per sale; no negative balance or total.

**Ready for what comes next.** `kind` is a column with a list of allowed values; withdrawals add theirs. `total_withdrawn` exists and stays at zero until then.

## Financial invariants covered (README §14)

| # | Invariant | How |
|---|---|---|
| 1, 2 | One revenue record per seller order | Unique constraint; tested by repeating the approval and by inserting directly |
| 3 | No duplicate wallet credit | Unique `(revenue record, kind)`; idempotent service; tested |
| 4 | Snapshots are used, not current terms | Amounts copied from the seller order; tested by changing the rate and plan before payment |
| 8 | Balances reconcile with their movements | `reconcile()`; tested against the stored rows |
| 9 | No client-side money | Read-only API; every write method returns `405`; tested |
| 12 | Nothing is deleted or edited to undo it | A reversal is a new movement; tested |
| 13 | Sellers' shares + commission = the payment | Tested on a multi-seller order with an amount that does not divide evenly |

## Security review

- [x] A seller reaches only their own wallet; another seller's, and all revenue, need staff permissions (`403`, tested).
- [x] No endpoint changes a balance.
- [x] Balances move only inside the transaction of a confirmed payment or an order step, never from request data.
- [x] Amounts come from the order's snapshot, never from the client.
- [x] The database refuses duplicates and negative balances even if the code is wrong.
- [x] Logs carry ids and the kind of movement, never amounts tied to names.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| **Sellers cannot withdraw** | The available balance cannot leave MUHUZE yet | Withdrawals, next |
| **No refunds** | A reversed sale's money is returned to the buyer by hand, and nothing records that it was | README §20 `R1`–`R4` |
| **A buyer who never confirms receipt** leaves the seller's money pending forever | A seller is not paid for a delivered order | README §20 `W10`: release automatically after a number of days, or let staff release |
| A released earning cannot be reversed | A complaint after receipt cannot be handled in the system | Refunds (`R3`) |
| No manual corrections by staff | A mistake needs a developer | An adjustment movement with a reason and its own permission |
| Subscription income is not in revenue | `/revenue/summary` shows commission only | When plan payments move into payments |
| No scheduled reconciliation | A mismatch would only be found by checking | A periodic job over `reconcile()` |

## Progress

- [x] Requirements and rules (this document, README §13)
- [x] Database design and migration `0009` (applied to the development database)
- [x] Models, repository, service, schemas, routes, permissions
- [x] Wired into orders: earning on payment, settlement on receipt, reversal on rejection
- [x] Tests written: `tests/api/wallets/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
