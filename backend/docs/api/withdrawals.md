# Withdrawals and Payout Destinations API

**Status:** implemented (`app/modules/withdrawals/`). Rules and rationale: [`docs/features/018_withdrawals.md`](../features/018_withdrawals.md).

All paths are under `/api/v1`, need `Authorization: Bearer <access token>`, and use the [standard envelope](response-format.md). Money is a decimal string in RWF.

Things to know up front:

- **The seller asks to be paid from money that is `available`** (see the [wallets API](wallets.md)). Pending money is never touchable.
- **Staff pay out by hand**, outside MUHUZE, and then record what they did. Nothing here moves real money (README §20 `W8`).
- A withdrawal's **destination is a snapshot** made at request time. Editing or deleting the saved destination never rewrites a past payout.

## For the seller: your withdrawals

Needs `withdrawal.request` (every seller has it). Requesting a new one needs an **active** seller; viewing and cancelling work in any status, even suspended.

| Method | Path | Purpose |
|---|---|---|
| POST | `/withdrawals` | Ask to be paid. `201` |
| GET | `/withdrawals/mine` | Your requests, newest first (`page`, `page_size`) |
| GET | `/withdrawals/mine/{withdrawal_id}` | One of your requests |
| POST | `/withdrawals/mine/{withdrawal_id}/cancel` | Call it off while it is `pending` |

**Request a withdrawal:**

```json
{
  "amount": "100000.00",
  "payout_destination_id": "3a2e…"
}
```

- `amount` — how much of your **available** balance; at least `1000.00`.
- `payout_destination_id` — one of your saved destinations.

The amount is **reserved** in the same transaction: it leaves `available_balance` immediately, and `total_withdrawn` only counts it once staff record the payout. A request against a deactivated destination is `400`; against a destination that is not yours, or does not exist, `404`.

**Withdrawal** (as the seller sees it):

```json
{
  "id": "9c1b…",
  "seller_id": "5b1e…",
  "amount": "100000.00",
  "currency": "RWF",
  "status": "pending",
  "destination_type": "mobile_money",
  "destination_provider": "MTN MoMo",
  "destination_account_number": "0788123456",
  "destination_account_name": "LAURA WAREHOUSE",
  "reason": null,
  "payout_reference": null,
  "created_at": "2026-10-08T12:00:00Z",
  "completed_at": null
}
```

| Field | Meaning |
|---|---|
| `status` | `pending` · `processing` · `completed` · `rejected` · `failed` · `cancelled` |
| `destination_*` | The account as it was when you requested — a snapshot |
| `reason` | Why staff rejected or failed it; `null` otherwise |
| `payout_reference` | The external payout id staff recorded, if any |

## For the seller: your payout destinations

Needs `payout_destination.manage` (every seller has it; works even while suspended).

| Method | Path | Purpose |
|---|---|---|
| POST | `/withdrawal/destinations` | Register an account. `201` |
| GET | `/withdrawal/destinations/mine` | Your accounts, active first |
| PATCH | `/withdrawal/destinations/{id}` | Update only the fields sent |
| POST | `/withdrawal/destinations/{id}/activate` | Make it choosable again |
| POST | `/withdrawal/destinations/{id}/deactivate` | Stop choosing it for new requests |
| DELETE | `/withdrawal/destinations/{id}` | Delete an account **no withdrawal ever used** |

**Create:**

```json
{
  "type": "mobile_money",
  "provider": "MTN MoMo",
  "account_number": "0788123456",
  "account_name": "LAURA WAREHOUSE"
}
```

`type` is `mobile_money` or `bank`; the rest is data only — MUHUZE validates nothing against the provider (README §20 `W8`).

Rules:

- **A used destination is never deleted.** `DELETE` on one is `409`; deactivate it instead. The deactivated account keeps its history.
- **A deactivated destination stops new requests** (`400`); staff files already out are unaffected.
- An update can set only the fields in the body; a `null` field is `422`.

## For staff

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/withdrawals` | `withdrawal.review` | Every request, newest first |
| GET | `/withdrawals/{withdrawal_id}` | `withdrawal.review` | One request, with review fields |
| POST | `/withdrawals/{withdrawal_id}/approve` | `withdrawal.review` | Accept: the payout may be made |
| POST | `/withdrawals/{withdrawal_id}/complete` | `withdrawal.review` | Record that the money reached the seller |
| POST | `/withdrawals/{withdrawal_id}/reject` | `withdrawal.review` | Decline; funds go back |
| POST | `/withdrawals/{withdrawal_id}/fail` | `withdrawal.review` | A payout that did not go through; funds go back |

`/withdrawals` accepts `status` (`pending` is the queue to review), `seller_id`, `page`, `page_size`.

**Staff response** adds the review trail:

```json
{
  "id": "9c1b…",
  "amount": "100000.00",
  "status": "processing",
  "reviewed_by_account_id": "2f7a…",
  "reviewed_at": "2026-10-08T13:00:00Z",
  "updated_at": "2026-10-08T13:05:00Z"
}
```

**The lifecycle** — a request is only ever in one of these, and staff act exactly in this order:

```
pending ──approve──► processing ──complete──► completed
   │                    │
   │                ───fail───► failed
   └──reject──► rejected
```

- **Approve** (`pending` → `processing`): staff now transfer the money by hand. The funds stay reserved.
- **Complete** (`processing` → `completed`): record the payout and count it in `total_withdrawn`. Optional body: `{"payout_reference": "MOMO-8821"}`.
- **Reject** (`pending` → `rejected`) / **Fail** (`processing` → `failed`): body `{"reason": "…"}` (5–500 characters, shown to the seller). The reserved funds return.
- The seller can **cancel** only a `pending` request; a wrong transition is `409`.
- **Repeating an action is safe.** Re-approving a `processing`, re-completing a `completed`, re-rejecting a `rejected`, or re-cancelling a `cancelled` request returns it unchanged — the ledger records nothing twice.

The wallet effects in ledger terms: requesting writes `withdrawal` (− available); approving writes nothing; completing writes a zero-balance `withdrawal_complete` and adds `total_withdrawn`; rejecting, failing, or cancelling writes `withdrawal_release` (+ available). See the [wallets API](wallets.md) for the movement shape.

## Errors

| Status | When |
|---|---|
| 400 | Amount below 1,000; more than the available balance; deactivated destination |
| 401 | No or invalid token |
| 403 | Missing permission; a buyer here; a suspended seller requesting; a seller opening staff endpoints |
| 404 | A withdrawal or destination that is not yours, or does not exist |
| 409 | Wrong transition; deleting a used destination; a second decision while one is in flight |
| 422 | A malformed id, amount, or page number |

## Example: the seller's whole flow

```
POST /withdrawal/destinations …                    → 201, saved
POST /withdrawals {amount, destination}             → 201, "pending"
     wallet: available − amount  (reserved)
staff: GET /withdrawals?status=pending               → the queue
staff: POST /withdrawals/{id}/approve                → "processing"
staff: POST /withdrawals/{id}/complete {reference}   → "completed"
     wallet: total_withdrawn + amount
```