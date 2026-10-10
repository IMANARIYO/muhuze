# 018 — Withdrawals and seller payout destinations

**Status:** `IN_PROGRESS`.

Business rules: [`README.md` §13.8](../../../README.md#138-withdrawals), [§14](../../../README.md#14-financial-invariants), [§15](../../../README.md#15-seller-verification-gates-withdrawals). API contract: [`docs/api/withdrawals.md`](../api/withdrawals.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

The only way money leaves MUHUZE for a seller. A seller asks to be paid their **available** balance to an account they registered; staff check it, pay it outside the system, and record the result. README build-order step 12: the last step before MUHUZE is fully operational on Phase 1.

## Scope

| In this feature | Not in this feature |
|---|---|
| Payout destinations: create, edit, deactivate | Any payment provider integration (`W8`: manual payout) |
| Withdrawal request, cancel, review, payout, failure | Fees, maximums, frequency limits (none, by decision) |
| Reserving and releasing funds in the wallet ledger | Refunds of any kind (`R1`–`R4`) |
| The seller approval gate on requests | Automatic processing (`W6`: all manual) |

## How it works

```
Seller has AVAILABLE funds                       (feature 012)
  │
  ├── registers a payout destination             mobile money / bank, data only
  │
  └── requests a withdrawal
        ├── wallet movement  "withdrawal"          − available   (reserves the funds)
        └── status: pending
  │
Staff with `withdrawal.review`
  ├── approve   pending → processing       (staff now pays out by hand)
  │     ├── complete  processing → completed   total_withdrawn += amount
  │     └── fail      processing → failed      + movement "withdrawal_release"
  ├── reject    pending → rejected             + movement "withdrawal_release"
  │
Seller (while pending)
  └── cancel    pending → cancelled             + movement "withdrawal_release"
```

The money is **reserved the moment the request is made**, so two requests (or a request and a purchase) can never spend the same funds. A rejected, failed, or cancelled request gives the funds back with a **new compensating movement**; nothing is edited or deleted.

## Rules

**Decided 2026-10-08** (README §13.8, §20 `W3`–`W6`, `W8`, `W9`, `S2`):

1. **No fee.** The seller receives the full requested amount; the wallet is debited exactly that amount.
2. **Minimum 1,000 RWF.** No maximum and no frequency limits today.
3. **All withdrawals require manual admin approval.** Seller requests → staff approve → staff pay out by hand → staff record completion or failure. Nothing is automatic.
4. **Destinations are mobile money or bank**, stored as data only (type, provider/bank, account number, holder name). No provider integration.
5. **No name-match check, no approval, and no cooling-off period** for destinations.
6. **Only an active, approved seller can request a withdrawal** (the same gate as selling, `get_active_seller`). A suspended seller must be reinstated first. Viewing, and cancelling your own pending request, stay possible in any status.
7. **Available funds only** (README §14, invariant 10): the request fails if the available balance is lower than the amount. Pending funds are never touchable.
8. **Destination snapshot.** Each withdrawal copies the destination's details at request time; later edits never rewrite where a past payout went. A destination that a withdrawal used is **deactivated, never deleted**.
9. **Lifecycle:** `pending → processing → completed`, with exits `rejected` and `failed` (staff) and `cancelled` (seller, while pending). A wrong transition is refused; repeating the same one changes nothing.
10. **Reasons are required** when staff reject or fail a request, and the seller sees them.
11. **Payout happens outside the system.** `complete` records the external payout reference, if staff have one.

**Ownership.** A withdrawal and a payout destination belong to one seller. Another seller's rows behave exactly like they do not exist (`404`), for reads and writes alike.

**Idempotency.** Every transition locks the withdrawal row first. Repeating an action on a withdrawal already in the target status returns it unchanged; acting from any other status is refused. The ledger's `unique (withdrawal, kind)` makes a double reserve or double release impossible even if the code were wrong.

## Who sees what

| Who | Sees |
|---|---|
| Seller | Their own destinations and withdrawals (`withdrawal.request`) |
| Staff with `withdrawal.review` | Every withdrawal, in every status; the review actions |
| Buyer | Nothing here |

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `withdrawal.request` | View and cancel your own withdrawals; request one | `seller` |
| `withdrawal.review` | List every withdrawal; approve, reject, complete, fail | – |
| `payout_destination.manage` | Manage your own payout destinations | `seller` |

## Design

```
app/modules/withdrawals/
├── withdrawal_routes.py          # /withdrawals, /withdrawal/destinations
├── withdrawal_dependencies.py
├── withdrawal_service.py         # rules above; calls the wallet ledger
├── withdrawal_repository.py
├── withdrawal_model.py           # SellerPayoutDestination, Withdrawal
├── withdrawal_schema.py
├── withdrawal_permissions.py
├── withdrawal_exceptions.py
└── withdrawal_constants.py
```

**How it uses other features** (always through their services, AGENTS.md §7):

| Need | Call |
|---|---|
| "May this account request a withdrawal?" | `get_current_active_seller` (permission first, then the active-seller gate) |
| Reserve, release, and record the payout | `WalletService.reserve_for_withdrawal` / `release_withdrawal` / `complete_withdrawal` — the ledger methods own every balance change |

**Ledger changes.** `wallet_transactions.revenue_transaction_id` becomes **nullable**: a sale movement points at a revenue record, a withdrawal movement at its withdrawal. Exactly one of the two is set (a database check). New kinds: `withdrawal` (− available) and `withdrawal_release` (+ available), enforced by the `kind` check constraint and `unique (withdrawal, kind)`.

**Locking.** The withdrawal row is locked for every transition, and the wallet row for every balance change, so a cancel and an approval can never both apply.

**Guaranteed by the database:** no negative balance (so funds can never be double-spent), at most one reserve and one release per withdrawal, a snapshot that is written once, and every status being a known one.

## Financial invariants covered (README §14)

| # | Invariant | How |
|---|---|---|
| 8 | Balances reconcile with their movements | Reserve/release are movements; `reconcile()` still holds; tested |
| 9 | No client-side money | The amount is validated, then debited under a wallet lock; the client never sets a balance |
| 10 | Available funds only | Checked against the locked balance; tested with pending-only funds |
| 12 | Nothing is deleted or edited to undo it | Release is a compensating movement; tested |
| 19 | Seller approval gate | `get_active_seller` on every request; tested with a suspended seller |
| 22 | Destination history | Snapshot columns on the withdrawal; tested by editing the destination afterwards |
| 23 | Separate destinations | Payout destinations are their own table; MUHUZE's payment destinations are never readable here |

## Security review

- [x] Permission first, then the active-seller gate, then ownership, on every endpoint.
- [x] A withdrawal request cannot be made for another seller, and another seller's destination is `404`.
- [x] Staff actions need `withdrawal.review`; sellers can never approve their own request.
- [x] Amount is validated server-side; the balance changes only inside the ledger under a row lock.
- [x] Payout destinations are never exposed to buyers or staff lists beyond what review needs.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| Payout is manual and unverified — staff can record a completion that did not happen | Human error | Provider integration (`W8`), reconciliation |
| No withdrawal fee, no limits, no frequency cap | None today; abuse possible | Revisit when abuse shows up |
| A destination can be edited while a request is pending | The pending request keeps its snapshot; the edited account is not used | None needed (snapshot) |
| No notification to staff when a request waits | Delayed payout | `014_notifications` |
| No statement of a seller's withdrawal history beyond the list | Support questions | Reporting (`016`) |

## Progress

- [x] Decisions recorded (README §13.8, §20: `W3`–`W6`, `W8`, `W9`, `S2`)
- [x] Requirements and rules (this document)
- [x] Database design and migration `0010`
- [x] Models, repository, service, schemas, routes, permissions
- [x] Wallet ledger methods for withdrawals
- [x] Tests written: `tests/api/withdrawals/`
- [ ] Full flow verified by hand against a real database
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
