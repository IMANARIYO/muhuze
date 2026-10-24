# Orders API

**Status:** implemented (`app/modules/orders/`). Rules and rationale: [`docs/features/010_orders.md`](../features/010_orders.md).

All paths are under `/api/v1`, need `Authorization: Bearer <access token>`, and use the [standard envelope](response-format.md). Money is a decimal string in RWF: `"850000.00"`.

## The cart is yours (frontend)

The backend has no cart. Keep the cart on the device (product ids and quantities), and at checkout send it as one request. **Do not send prices or totals**: the backend reads every price itself, and anything else in the request is ignored. Show the buyer the totals from the response.

**Services are not checked out.** A listing with `kind: "service"` cannot go in the cart: checkout refuses it (`422`). The buyer sends a [service request](service_requests.md) instead, and when the provider accepts it an order of `kind: "service"` is created here for the buyer to pay. From then on it is paid, cancelled while unpaid, and confirmed with the endpoints below, like any order.

## For the buyer

Needs a login only. Every path reaches only the caller's own orders.

| Method | Path | Purpose |
|---|---|---|
| POST | `/orders` | Check out (201) |
| GET | `/orders/mine` | Your orders, newest first. `status`, `page`, `page_size` |
| GET | `/orders/mine/{order_id}` | One order with each shop's part |
| POST | `/orders/mine/{order_id}/cancel` | Cancel it, while unpaid. Body: `{}` or `{ "reason": "…" }` |
| POST | `/orders/mine/{order_id}/seller-orders/{seller_order_id}/confirm-receipt` | Say one shop's part arrived |

**Check out**

```json
{
  "items": [
    { "product_id": "e41a…", "quantity": 1 },
    { "product_id": "77b0…", "quantity": 2 }
  ],
  "delivery": {
    "recipient_name": "Carol Mukamana",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
    "address": "KK 15 Rd, blue gate"
  },
  "note": "Call before delivery"
}
```

| Field | Rule |
|---|---|
| `items` | 1 to 50; each product once (use `quantity`) |
| `quantity` | 1 to 999 |
| `delivery.recipient_name` | 1 to 150 characters |
| `delivery.recipient_phone` | E.164 |
| `delivery.province`, `district`, `sector` | Required |
| `delivery.address` | Optional, up to 255 characters |
| `note` | Optional, up to 500 characters; the sellers see it |

**Order** (the buyer's view):

```json
{
  "id": "0c9d…",
  "order_number": "MHZ-000123",
  "kind": "product",
  "scheduled_for": null,
  "status": "in_progress",
  "currency": "RWF",
  "total_amount": "1305000.00",
  "paid_at": "2026-10-07T12:00:00Z",
  "cancelled_at": null,
  "cancel_reason": null,
  "created_at": "2026-10-07T11:50:00Z",
  "delivery": { "recipient_name": "Carol Mukamana", "…": "…", "note": "Call before delivery" },
  "seller_orders": [
    {
      "id": "51fa…",
      "seller_id": "3f0c…",
      "seller_name": "Amina Shop",
      "status": "shipped",
      "status_reason": null,
      "subtotal": "855000.00",
      "items": [
        {
          "id": "9a20…",
          "product_id": "e41a…",
          "product_name": "Galaxy S24",
          "unit_price": "850000.00",
          "quantity": 1,
          "line_total": "850000.00",
          "image_url": "https://res.cloudinary.com/…",
          "attributes": [ { "name": "Storage", "value": 256, "unit": "GB" } ]
        }
      ]
    }
  ]
}
```

- **Show the order from this data, not from the live product.** `product_name`, `unit_price`, `image_url`, and `attributes` are what the buyer bought; the product may have changed since. Use `product_id` only for a "view product" link.
- The list endpoint returns the fields down to `created_at` only.
- `kind` is `product` (a checkout) or `service` (an accepted service request: one shop, one item). A service order has `scheduled_for`, the agreed time, and `delivery` is where the service happens.

**Order status:** `awaiting_payment` → `in_progress` → `completed`, or `cancelled`.

**Each shop's part** has its own status. Show them separately:

| `status` | Meaning for the buyer |
|---|---|
| `awaiting_payment` | Not paid yet |
| `pending` | Paid; the shop has not responded |
| `accepted` | The shop is preparing it |
| `shipped` | On its way. **The buyer can now confirm receipt** (goods only) |
| `delivered` | The shop says it arrived. For a service: the provider says it was **done**. Ask the buyer to confirm |
| `completed` | The buyer confirmed |
| `rejected` | The shop declined, or the provider cannot do a paid service; `status_reason` says why |

A **service** order skips `pending` and `shipped`: once paid it is `accepted` (the provider already accepted the request), then `delivered` when the provider marks it done. The buyer can confirm it only after that.
| `cancelled` | The order was cancelled before payment |

## For the seller

Needs a login, the `seller_order.manage` permission (every seller has it), and an **active** seller. A seller sees only their own shop's part of an order, and only once the order is paid.

| Method | Path | Purpose |
|---|---|---|
| GET | `/seller-orders/mine` | Your shop's paid orders, newest first. `status`, `page`, `page_size`. New work is `status=pending` |
| GET | `/seller-orders/mine/{seller_order_id}` | One order: items, where to deliver, what you earn, history |
| POST | `/seller-orders/mine/{seller_order_id}/accept` | Goods: `pending` → `accepted` |
| POST | `/seller-orders/mine/{seller_order_id}/reject` | Goods: `pending` → `rejected`. Service: `accepted` → `rejected` (you cannot do it after all). Body: `{ "reason": "…" }` (5 to 500 characters; the buyer sees it). The buyer is owed a refund (manual) |
| POST | `/seller-orders/mine/{seller_order_id}/ship` | Goods: `accepted` → `shipped` |
| POST | `/seller-orders/mine/{seller_order_id}/deliver` | Goods: `shipped` → `delivered` |
| POST | `/seller-orders/mine/{seller_order_id}/mark-done` | Service: `accepted` → `delivered` (done). The buyer then confirms |

**Seller order:**

```json
{
  "id": "51fa…",
  "order_id": "0c9d…",
  "order_number": "MHZ-000123",
  "kind": "product",
  "scheduled_for": null,
  "seller_id": "3f0c…",
  "status": "pending",
  "status_reason": null,
  "currency": "RWF",
  "subtotal": "855000.00",
  "commission_rate": "7.50",
  "commission_amount": "64125.00",
  "seller_amount": "790875.00",
  "plan_name": "Business",
  "recipient_name": "Carol Mukamana",
  "paid_at": "2026-10-07T12:00:00Z",
  "created_at": "2026-10-07T11:50:00Z",
  "delivery": { "recipient_name": "…", "recipient_phone": "…", "province": "…", "district": "…", "sector": "…", "address": "…", "note": "…" },
  "items": [ { "…": "as in the buyer's view" } ],
  "events": [
    { "from_status": "awaiting_payment", "to_status": "pending", "reason": null, "actor_account_id": null, "created_at": "…" }
  ]
}
```

- `seller_amount` is what the seller earns from this order; `commission_amount` is MUHUZE's share. `plan_name` is the plan that gave the rate, or `null` for the default rate.
- `events` is the history. `actor_account_id` is `null` when the system did it (payment confirmed).
- The list returns `id`, `order_number`, `kind`, `scheduled_for`, `status`, `currency`, `subtotal`, `seller_amount`, `recipient_name`, `paid_at`, `created_at`.

## For staff

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/orders` | `order.read` | Every order. `status`, `buyer_account_id`, `q` (order number), `page`, `page_size` |
| GET | `/orders/{order_id}` | `order.read` | Any order in full: every part with its money split and history |

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | Seller or staff endpoint without the permission |
| 403 | `Only an approved, active seller can do this` | The seller is suspended, closed, or not approved |
| 404 | `Order not found` | Unknown id, **someone else's order**, another shop's part, or (for a seller) an unpaid order |
| 409 | `A paid order cannot be cancelled` / `This order is already cancelled` | Cancel |
| 409 | `Only an order that is pending can be accepted` (and the like) | A step out of order |
| 409 | `You can confirm receipt once the seller has shipped it` | Confirming too early, or twice |
| 409 | `You can confirm the service once the provider has marked it done` | Confirming a service too early, or twice |
| 409 | `A service order cannot be shipped` / `A product order cannot be marked done` (and the like) | A step that does not apply to this kind of order |
| 422 | `Services are booked by sending a request to the provider, not through checkout: <names>` | A service in the cart; nothing was ordered |
| 422 | `These products are no longer available: <ids>` | One or more products are not on sale; nothing was ordered. Remove them from the cart and try again |
| 422 | `You cannot order products from your own shop` | |
| 422 | `MUHUZE has not set its commission rate yet` | Staff have not set the default rate |
| 422 | field errors | Request validation |
