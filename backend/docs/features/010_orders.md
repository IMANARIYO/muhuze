# 010 — Orders

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §8, §9, §11](../../../README.md#8-cart-and-checkout). API contract: [`docs/api/orders.md`](../api/orders.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Turn a buyer's cart into a purchase: record exactly what was bought, at what price, from which shops, and how the money for each shop is split between the seller and MUHUZE. Payments, revenue, wallets, and withdrawals are all built on what is recorded here.

## Shape

```
Order MHZ-000123            the buyer's whole purchase; what gets paid
  ├── SellerOrder  Amina Shop     own status, own money split
  │     ├── Galaxy S24 × 1
  │     └── Phone case × 2
  └── SellerOrder  Brian Shop
        └── Laptop × 1
```

One checkout is always **one order**, however many shops are involved. It is never split into several orders, and never modelled as belonging to one seller (README §6.1).

## Rules

**The cart lives in the frontend** (decided 2026-10-07, `X8`). The backend has no cart. `POST /orders` receives only **product ids and quantities**, plus where to deliver.

**Placing an order** happens in one transaction: the whole order exists, or none of it does.

1. Every product is read from the database **as a buyer can see it right now**. A product that is not on sale (draft, archived, hidden, its shop closed, its category off) makes the whole order fail, naming every such product.
2. Prices, totals, sellers, and statuses sent by the client are **ignored**: the request schema does not even have those fields.
3. Items are grouped by shop. For each shop, the commission terms in force at that moment are resolved by the seller plans feature and **copied onto the seller order**.
4. Totals are computed bottom up: line total → seller subtotal → order total.

**Snapshots** (README §11). An order never changes because something else did:

| Recorded on the order | So later changes to this don't matter |
|---|---|
| Product name, unit price, picture, details | the product |
| Shop name | the seller |
| Commission rate, MUHUZE's amount, the seller's amount, and which subscription or default rate gave the rate | the seller's plan, the plan itself, the default rate |
| Recipient, phone, address | the buyer's details |

**Decided 2026-10-07** (README §20):

1. **The total is the sum of the items.** MUHUZE adds no delivery fee, discount, or tax for now; delivery is arranged between the buyer and each seller (`O6`, `C8`, `T1` stay open for when that changes).
2. **Commission = seller subtotal × rate, rounded half up to the cent.** The seller receives the subtotal minus the commission, so the two always add up exactly and any rounding remainder goes to the seller (`C13`).
3. **A seller sees their part only once the order is paid** (`O3`).
4. **Prepaid only.** No cash on delivery (`P8`).
5. **The buyer can cancel the whole order while it is unpaid.** An unpaid order does not expire on its own for now (`P3`).
6. **After payment each shop handles its part independently.** The seller can reject while it is pending; the buyer confirms receipt to complete it.
7. **No cancelling single items.** A seller accepts or rejects their whole part (`O2`).
8. **The order's status is derived from its parts** (`O1`), table below.
9. **A buyer cannot order from their own shop.** At most 50 different products per order, quantity 1 to 999 each.

**A seller order's life**

```
awaiting_payment ──(payment confirmed)──► pending ──accept──► accepted ──ship──► shipped ──deliver──► delivered
       │                                     │                                       │                    │
       │ buyer cancels                       │ reject (with a reason)                └── buyer confirms ──┴──► completed
       ▼                                     ▼
   cancelled                             rejected
```

- Steps cannot be skipped or repeated. Each is recorded with who did it and when.
- The buyer can confirm receipt as soon as it is `shipped`; they need not wait for the seller to mark it delivered.
- `completed`, `rejected`, and `cancelled` are final.

**The order's status** is worked out by one function, `derive_order_status`, every time a part changes, in the same transaction. Nothing else sets it.

| Situation | Order status |
|---|---|
| Cancelled by the buyer before payment | `cancelled` |
| Not paid yet | `awaiting_payment` |
| Paid, and at least one shop's part is not final | `in_progress` |
| Every part is final, and at least one was completed | `completed` |
| Every part is final, and none was completed (all rejected) | `cancelled` |

Payment status is a separate matter and belongs to the payments feature; here an order only knows whether it has been paid (`paid_at`).

**Who sees what**

| | Sees |
|---|---|
| Buyer | Their own orders: every shop's part, items, and status. **Never** commission or seller earnings |
| Seller | Their own shop's part of paid orders: items, where to deliver, their money split. **Never** another shop's part or the order total |
| Staff with `order.read` | Everything |

An order or part that isn't yours is "not found".

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `seller_order.manage` | See and handle the paid orders of your own shop | `seller` |
| `order.read` | See every order in full, including each shop's commission and earnings | – |

Placing an order and managing your own orders need only a login: every account can buy.

## Design

```
app/modules/orders/
├── order_routes.py        # /orders (buyer, staff), /seller-orders/mine (seller)
├── order_dependencies.py
├── order_service.py       # place_order, mark_paid, status changes, derive_order_status, split_commission
├── order_repository.py
├── order_model.py         # Order, SellerOrder, OrderItem, SellerOrderEvent
├── order_schema.py
├── order_permissions.py
├── order_exceptions.py
└── order_constants.py
```

**What orders ask other features** (always through their services):

| Need | Call |
|---|---|
| A product as a buyer sees it now | `ProductService.get_public_product` |
| The commission terms for a seller | `SellerPlanService.resolve_commercial_terms` |
| The buyer's own shop, if any | `SellerService.find_seller_id` |

**For the payments feature.** `OrderService.mark_paid(order_id)` records the payment and releases each part to its seller. It does **not** commit, so payment confirmation and order release are one transaction, and it is **idempotent**: a repeated confirmation changes nothing. A cancelled order cannot be paid.

**Guaranteed by the database**, whatever the application does: the commission and seller amounts add up to the subtotal; a line total equals price × quantity; every seller order records exactly one source for its rate; a shop appears once per order and a product once per shop's part.

**Order numbers** (`MHZ-000123`) come from a database sequence, so two orders can never share one. An order that fails to save leaves a gap in the numbering; that is harmless.

**Concurrency.** Every status change locks the order row first, so two changes to the same order, or to two of its parts, happen one at a time and the derived status is always right.

## Security review

- [x] The client cannot set a price, total, seller, or status: the request has no such fields, and extras are ignored (tested).
- [x] Only products a buyer can see right now can be ordered.
- [x] A buyer reaches only their own orders; a seller only their own shop's part, and only after payment.
- [x] The buyer never sees commission or seller earnings; a seller never sees another shop's part or the order total.
- [x] Staff views need `order.read`.
- [x] The money split is computed once, with exact decimals, and checked by the database.
- [x] A paid order cannot be cancelled by the buyer; a cancelled order cannot be paid.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| **A rejected part of a paid order needs a refund, and nothing does it** | The buyer has paid for something they won't receive; staff must refund by hand | Refund rules: README §20 `R1`–`R3` |
| No stock, by decision | Two buyers can order the last unit; the seller rejects one | See the refund gap above |
| Unpaid orders never expire | Old unpaid orders pile up | README §20 `P3` |
| A seller who never responds leaves a part `pending` forever | The buyer waits | README §20 `O4` (auto-cancel) |
| A part marked `delivered` stays so until the buyer confirms | Earnings could be held up by a buyer who never confirms | Auto-complete after a number of days (README §20 `W10`) |
| A suspended seller cannot handle orders already paid | Those buyers are stuck | README §20 `S2`; staff tools |
| Placing an order reads each product separately | Slower for very large carts | Batch the read if carts get large |
| No notifications | Sellers must check the app for new orders | `014_notifications` |

## Progress

- [x] Requirements and rules (this document, README §8, §9, §11)
- [x] Database design and migration `0007` (applied to the development database)
- [x] Models, repository, service, schemas, routes, permissions
- [x] Snapshots of product and commercial terms
- [x] The `mark_paid` hook for payments
- [x] Tests written: `tests/api/orders/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
