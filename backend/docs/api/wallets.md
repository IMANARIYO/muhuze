# Wallets and Revenue API

**Status:** implemented (`app/modules/wallets/`). Rules and rationale: [`docs/features/012_wallets.md`](../features/012_wallets.md).

All paths are under `/api/v1`, need `Authorization: Bearer <access token>`, and use the [standard envelope](response-format.md). Money is a decimal string in RWF, always with two decimal places.

**Everything here is read-only.** Balances change only when a payment is confirmed or an order moves; no request can set one. `POST`, `PUT`, `PATCH`, and `DELETE` return `405`.

## For the seller

Needs `wallet.read_own` (every seller has it). Works for any seller account, including a suspended one.

| Method | Path | Purpose |
|---|---|---|
| GET | `/wallet/mine` | Your balances |
| GET | `/wallet/mine/transactions` | Every movement, newest first (`page`, `page_size`) |

**Wallet**

```json
{
  "seller_id": "5b1e…",
  "currency": "RWF",
  "pending_balance": "405000.00",
  "available_balance": "94499.99",
  "total_earned": "499499.99",
  "total_withdrawn": "0.00"
}
```

| Field | Meaning | Show it as |
|---|---|---|
| `pending_balance` | Paid sales the buyer has not yet confirmed receiving | "On the way" — cannot be withdrawn |
| `available_balance` | Sales the buyer confirmed | "Ready to withdraw" |
| `total_earned` | Everything earned so far, less what was reversed | |
| `total_withdrawn` | Everything paid out so far | |

A seller with no sales yet gets the same shape with zeros, not an error.

This is what MUHUZE **owes** the shop. Do not word it as money the seller already holds.

**Movement**

```json
{
  "id": "c2a4…",
  "kind": "settlement",
  "pending_change": "-94499.99",
  "available_change": "94499.99",
  "pending_after": "0.00",
  "available_after": "94499.99",
  "order_id": "0c9d…",
  "seller_order_id": "e7f1…",
  "created_at": "2026-10-07T12:00:00Z"
}
```

| `kind` | When | Effect |
|---|---|---|
| `earning` | The buyer's payment was confirmed | + pending |
| `settlement` | The buyer confirmed receipt | pending → available |
| `reversal` | The seller rejected an order that was already paid | − pending |

`*_change` is signed; `*_after` is the balance once the movement was applied. Link a movement to its order with `seller_order_id`.

## For staff

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/wallets/{seller_id}` | `wallet.read` | A seller's balances |
| GET | `/wallets/{seller_id}/transactions` | `wallet.read` | A seller's movements |
| GET | `/revenue` | `revenue.read` | The revenue record of each sale, newest first |
| GET | `/revenue/summary` | `revenue.read` | Totals |

`/revenue` accepts `seller_id`, `order_id`, `page`, `page_size`. `/revenue/summary` accepts `seller_id`.

**Revenue record** (one per shop per paid order):

```json
{
  "id": "91d0…",
  "seller_order_id": "e7f1…",
  "order_id": "0c9d…",
  "seller_id": "5b1e…",
  "gross_amount": "104999.99",
  "commission_rate": "10.00",
  "commission_amount": "10500.00",
  "seller_amount": "94499.99",
  "currency": "RWF",
  "reversed_at": null,
  "created_at": "2026-10-07T12:00:00Z"
}
```

`gross_amount` is what the buyer paid for that shop's part; `commission_amount` is MUHUZE's income; `seller_amount` is the seller's share. The two always add up to the gross. `reversed_at` is set if the sale was undone.

**Summary**

```json
{
  "sales": 3,
  "gross_amount": "1004999.99",
  "commission_amount": "100500.00",
  "seller_amount": "904499.99",
  "currency": "RWF"
}
```

Reversed sales are left out. `commission_amount` is what MUHUZE earned from commission; subscription income is not included.

## Errors

| Status | When |
|---|---|
| 401 | No or invalid token |
| 403 | Missing permission; a buyer opening `/wallet/mine`; a seller opening another seller's wallet or revenue |
| 405 | Any attempt to write |
| 422 | A malformed id or page number |
