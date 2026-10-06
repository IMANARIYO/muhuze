# Payments API

**Status:** implemented (`app/modules/payments/`), Phase 1 (manual). Rules and rationale: [`docs/features/011_payments.md`](../features/011_payments.md).

All paths are under `/api/v1`, need `Authorization: Bearer <access token>`, and use the [standard envelope](response-format.md). Money is a decimal string in RWF.

## For the buyer

Needs a login only, and reaches only the caller's own orders.

| Method | Path | Purpose |
|---|---|---|
| GET | `/orders/mine/{order_id}/payment` | How to pay, and what has been submitted |
| POST | `/orders/mine/{order_id}/payment` | "I have paid": submit the transaction reference (201) |

**The payment screen**

1. `GET …/payment`. Show `amount` and the accounts in `pay_to` (the default is first).
2. The buyer pays MUHUZE with their mobile-money app or bank, outside this app.
3. They type the transaction reference from the confirmation message; `POST …/payment`.
4. Show "waiting for confirmation". Poll `GET …/payment` or the order until its status changes.

**Instructions**

```json
{
  "order_id": "0c9d…",
  "order_number": "MHZ-000123",
  "amount": "850000.00",
  "currency": "RWF",
  "can_pay": true,
  "pay_to": [
    {
      "id": "aa11…",
      "method": "mobile_money",
      "provider": "…",
      "account_reference": "…",
      "registered_name": "…",
      "instructions": "…",
      "is_default": true
    }
  ],
  "attempts": []
}
```

- Tell the buyer to check that the name shown when they pay matches `registered_name`.
- `can_pay` is `true` only when a payment can be submitted now. It is `false` while one is waiting to be verified, once the order is paid or cancelled, or if MUHUZE has no active account.
- `pay_to` is empty unless the order is waiting for payment.
- `attempts` are the payments submitted so far, newest first. If the latest is `rejected`, show its `rejection_reason` and let the buyer try again.

**Submit**

```json
{
  "destination_id": "aa11…",
  "reference": "MP240001.ABCD",
  "payer_phone": "+250788111222",
  "payer_name": "Carol Mukamana"
}
```

| Field | Rule |
|---|---|
| `destination_id` | One of the `pay_to` accounts |
| `reference` | 3 to 100 characters: the transaction id from the confirmation message |
| `payer_phone` | E.164: the number the money was sent from |
| `payer_name` | Up to 150 characters: the name on the paying account |

Send `payer_phone`, `payer_name`, or both; at least one is required. **Do not send an amount**: it is always the order's total.

**Payment** (the buyer's view):

```json
{
  "id": "7f3e…",
  "order_id": "0c9d…",
  "status": "awaiting_verification",
  "amount": "850000.00",
  "currency": "RWF",
  "reference": "MP240001.ABCD",
  "destination_method": "mobile_money",
  "destination_provider": "…",
  "destination_account_reference": "…",
  "destination_registered_name": "…",
  "rejection_reason": null,
  "paid_at": null,
  "created_at": "2026-10-07T12:00:00Z"
}
```

`status`: `awaiting_verification` → `paid`, or `rejected`. Submitting never pays the order by itself.

## For staff: verifying payments

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/payments` | `payment.verify` | Every payment, longest-waiting first. `status`, `q`, `page`, `page_size` |
| GET | `/payments/{payment_id}` | `payment.verify` | One payment |
| POST | `/payments/{payment_id}/approve` | `payment.verify` | The money arrived: mark it paid and release the order |
| POST | `/payments/{payment_id}/reject` | `payment.verify` | It did not. Body: `{ "reason": "…" }` (5 to 500 characters; the buyer sees it) |

- The work queue is `status=awaiting_verification`.
- `q` searches the transaction reference and the order number (contains, case-insensitive).
- **Before approving**, check MUHUZE's actual statement for the reference, the amount, the date, the account, and the sender.
- Approving is safe to repeat: a second approval returns the same paid payment and changes nothing.

The staff view adds to the buyer's fields: `order_number`, `payer_account_id`, `payer_name`, `payer_phone`, `channel`, `verified_by_account_id`, `verified_at`.

## For staff: MUHUZE's receiving accounts

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/payment-destinations` | `payment_destination.manage` | All accounts, active first |
| POST | `/payment-destinations` | `payment_destination.manage` | Add one (201) |
| PATCH | `/payment-destinations/{id}` | `payment_destination.manage` | Change its details |
| POST | `/payment-destinations/{id}/activate` | `payment_destination.manage` | Show it to buyers again |
| POST | `/payment-destinations/{id}/deactivate` | `payment_destination.manage` | Stop showing it; it also stops being the default |
| POST | `/payment-destinations/{id}/set-default` | `payment_destination.manage` | Show it first; replaces the current default |
| DELETE | `/payment-destinations/{id}` | `payment_destination.manage` | Delete one no payment ever used |

```json
{
  "method": "mobile_money",
  "provider": "…",
  "account_reference": "…",
  "registered_name": "…",
  "instructions": "…",
  "is_default": true
}
```

| Field | Rule |
|---|---|
| `method` | `mobile_money`, `merchant_code`, `bank_transfer` |
| `provider` | 1 to 100 characters: the network or bank, as buyers know it |
| `account_reference` | 1 to 100 characters: the phone number, merchant code, or account number |
| `registered_name` | 1 to 150 characters: the name buyers see when paying |
| `instructions` | Optional, up to 500 characters |
| `is_default` | Optional, on creation only; use `set-default` afterwards |

Changing an account never changes a payment already made to it.

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | Staff endpoint without the permission |
| 404 | `Order not found` | Unknown order, or someone else's |
| 404 | `Payment not found` / `Payment destination not found` | Unknown id |
| 409 | `This order is not waiting for payment` | Submitting for a paid or cancelled order |
| 409 | `A payment for this order is already waiting to be verified` | A second submission |
| 409 | `This transaction reference has already been used` | The reference belongs to another payment |
| 409 | `Only a payment awaiting verification can be approved` (or `rejected`) | Wrong status |
| 409 | `A cancelled order cannot be paid` | Approving after the buyer cancelled; reject the payment and refund outside the system |
| 409 | `Payments have used this destination. Deactivate it instead of deleting it.` | Delete |
| 422 | `This payment destination is not available. Choose one of the listed accounts.` | Unknown or inactive `destination_id` |
| 422 | `You cannot verify a payment you made yourself` | Approve or reject |
| 422 | `Only an active destination can be the default` | `set-default` |
| 422 | field errors | Request validation |
