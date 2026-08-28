# MUHUZE Commerce Design — Cart → Order → Payment → Fulfillment

Status: **Implemented** (with mobile money / Airtel Money via a stub gateway) — this
supersedes the earlier `financial-flow-design.md` scope with the full **commerce** scope
agreed below.

Approved direction (per discussion):
- Build **Cart → Checkout → Order → Payment → Seller fulfillment → Shipping/Delivery → Completion**.
- Backend is the source of truth; the frontend only requests and displays — it never computes money.
- **Multi-seller** is a first-class architecture constraint (one checkout, many seller orders).
- **Order-level shipping snapshot** — orders never depend on a live address record.
- Leave for later: wishlist, favorites, reviews, recommendations, comparison, advanced promotions.
- Commit/currency stays single: `RWF` (Numeric(12,2)).

---

## 1. One complete purchase (the walkthrough we'll design around)

```
Add to Cart → Checkout → Order created → Payment confirmed (Paid)
   → Seller A receives → accepts → prepares → hands to delivery
   → delivered → completed
```

Plus the unhappy paths: seller rejects → seller order cancelled → partial refund; buyer
cancels before payment; payment fails.

## 2. Table & relationship design (walk through before writing models)

All models live in the standard 4-layer module shape (`router → controller → service →
repository → schemas → exceptions → dependencies`) and are registered in
`app/db/models.py`.

### 2.1 `cart_items` (module: `carts`)

A cart is **implicit** (rows keyed by account) — no separate `cart` table in v1.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `account_id` | UUID FK → accounts | the buyer |
| `listing_id` | UUID FK → seller_listings | **the specific seller's offer** being bought |
| `quantity` | Integer | >= 1 |
| `created_at` / `updated_at` | mixin | |

Unique key: `(account_id, listing_id)` — one row per account+listing; adding again bumps
quantity. Referencing `seller_listings` (not the variant) is deliberate: the customer buys
**a specific seller's offer at a specific price**, exactly what order-items later snapshot.

### 2.2 `shipping_addresses` (module: `addresses`)

The customer's address **book** — editable and mutable, and **never referenced directly as
the delivery destination by an order** (orders use the immutable `shipping_infos` snapshot).

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `account_id` | UUID FK → accounts | |
| `label` | String | Home / Work / Other |
| `recipient_name` | String | who to hand it to |
| `phone` | String | delivery recipient phone (separate from `accounts.phone`) |
| `country` / `province` / `district` / `sector` / `cell` / `village` | String | Rwanda address hierarchy |
| `address_line` | String | street / building / landmarks |
| `delivery_instructions` | String | e.g. "call on arrival", "after 6pm" |
| `latitude` / `longitude` | Numeric | for future delivery + nearby-seller |
| `is_default` | Boolean | one default per account |
| timestamps | mixin | |

### 2.3 `orders` (module: `orders`)

**The order belongs to the BUYER, never a seller.** One checkout can span many sellers; each
`order_item` carries its own `seller_id`, so the backend always knows who must fulfill what
— even though it reads as a single order to the customer. All money is **GROSS** (what the
buyer pays), captured as snapshots at checkout.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_number` | String, unique | human-readable, e.g. `MUH-2026-000123` |
| `buyer_account_id` | UUID FK → accounts | the buyer |
| `status` | String enum | order lifecycle: `pending` / `cancelled` |
| `payment_status` | String enum | `pending / paid / failed / refunded / partially_refunded` — sourced from payments |
| `shipping_address_id` | UUID FK → shipping_addresses | which saved address was picked (for reference only) |
| `shipping_info_id` | UUID FK → shipping_infos | **the immutable snapshot actually used for delivery** |
| `contact_phone` | String | captured at checkout, separate from `accounts.phone` |
| `subtotal` | Numeric(12,2) | sum of `order_items.subtotal` |
| `shipping_fee` | Numeric(12,2) | total delivery fee across sellers |
| `discount_amount` | Numeric(12,2) | promo discount (0 for now) |
| `total_amount` | Numeric(12,2) | subtotal + shipping_fee − discount_amount |
| `currency` | String | `RWF` |
| `notes` | String | buyer order notes |
| timestamps | mixin | incl. `paid_at`, `completed_at` |

The commission split is derived at the revenue step, never stored redundantly on the order.

### 2.4 `order_items` (module: `orders`)

Preserves the **exact purchase at the moment of ordering** (the snapshot principle). Owned by
an **order**.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_id` | UUID FK → orders | |
| `seller_id` | UUID FK → sellers | which seller fulfills/earns this line — the multi-seller key |
| `listing_id` | UUID FK → seller_listings | the exact seller offer bought |
| `product_variant_id` | UUID FK → product_variants | |
| `product_name` | String | **snapshot**, never a live join — see note below |
| `variant_name` | String | e.g. `128GB / Black` |
| `unit_price` | Numeric(12,2) | **snapshot** from the listing at purchase |
| `quantity` | Integer | |
| `subtotal` | Numeric(12,2) | unit_price × quantity |

> **Why the snapshot:** seller A sells a phone for 150000 today and raises it to 170000
> tomorrow. The completed order must still say 150000 — so `order_items` copies
> `product_name` / `variant_name` / `unit_price` at purchase instead of trusting the live
> product/listing rows. This is the single most important ecommerce-schema concept, and it
> is built in from the start.

### 2.5 `seller_orders` (module: `orders`) — **implemented**

The per-seller **fulfillment** grouping (one `seller_orders` row per distinct seller, so
Seller A never sees Seller B's items). Rows are created **at payment time** — in the same DB
transaction as revenue derivation, when `Payments → paid` — **not** at checkout. Each row
carries its own status driven by the seller endpoints (`POST /api/v1/orders/seller/...`).

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_id` | UUID FK → orders | which buyer order this fulfills |
| `seller_id` | UUID FK → sellers | which seller fulfills this group |
| `status` | String enum | `pending → accepted → shipped → delivered`, `pending → rejected`, any → `cancelled` |
| `rejected_reason` | Text, nullable | set when the seller rejects |
| `accepted_at` / `shipped_at` / `delivered_at` | datetime, nullable | set on the corresponding transition |
| timestamps | mixin | |

Unique key: `(order_id, seller_id)` named `uq_seller_orders_order_seller` — one row per
seller per order, guarding against duplicate fulfillment rows. `order_id`, `seller_id`, and
`status` are each indexed. `cancel` is part of the state machine but not yet exposed via the
endpoints.

### 2.6 `shipping_infos` (module: `orders` or `shipping`) — Phase 1

**Immutable, order-owned snapshot** of the delivery destination — copied from the chosen
`shipping_addresses` row at checkout so later edits to the address book never change past
orders.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_id` | UUID FK → orders (nullable until checkout) | |
| `recipient_name` | String | |
| `phone` | String | the delivery recipient's phone (delivery to mother, call her) |
| `country` / `province` / `district` / `sector` / `cell` / `village` | String | |
| `address_line` | String | |
| `delivery_instructions` | String | |
| `latitude` / `longitude` | Numeric | |
| timestamps | mixin | |

### 2.7 `payments` (module: `payments`, kept separate from orders)

One payment per order. Lives in its own module so payment logic isn't tangled into orders.
Payments use a **mobile money (Airtel Money) stub gateway**: `payments/gateway.py` defines a
`MomoGateway` protocol plus a `StubMomoGateway` behind a `get_momo_gateway()` factory, which
a real Airtel/MTN adapter must replace.

**Lifecycle:** `create` calls the gateway's `request_payment`, which returns a
`request_reference` (e.g. `MOMO-XXXXXXXXXXXX`) stored as `provider_ref`; the order stays
`pending`. The gateway then calls `POST /payments/{id}/paid`, which confirms via
`confirm_payment` and, **in the same DB transaction**, derives the revenue transaction **and**
creates the per-seller `seller_orders` rows → the order flips to `paid`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_id` | UUID FK → orders | |
| `status` | String enum | `pending → paid → failed → refunded` |
| `amount` | Numeric(12,2) | = order total |
| `currency` | String | `RWF` |
| `method` | String | `airtel_money` |
| `provider_ref` | String | the gateway's `request_reference`, e.g. `MOMO-XXXXXXXXXXXX` |
| `momo_phone` | String(20), nullable | buyer's Airtel Money wallet to charge |
| `airtel_phone` | String(20), nullable | the Airtel line the payment is sent from |
| `paid_at` | datetime | set on `Paid` |
| timestamps | mixin | |

### 2.8 `revenue_transactions` (module: `revenue`)

The single accounting record — created **exactly once**, in the same transaction as
`Payment → Paid`. One per order in v1 (or per seller-order if per-seller pricing differs;
recommend: one per order with a seller-earning breakdown).

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `order_id` | UUID FK → orders | **unique** (idempotency / "never duplicated") |
| `payment_id` | UUID FK → payments | |
| `seller_id` | UUID FK → sellers | |
| `amount` | Numeric(12,2) | gross from that seller |
| `revenue_rate` | Numeric(5,2) | **7% premium / 12% basic snapshot** |
| `commission_amount` | Numeric(12,2) | MUHUZE cut |
| `seller_earning` | Numeric(12,2) | net to seller → future wallet |
| `currency` | String | `RWF` |
| `referral_eligible` | Boolean | placeholder — future referrals, from premium plan flag |
| timestamps | mixin | |

### 2.9 `shipments` (module: `delivery`) — **implemented**

Delivery as its own concern so a future driver/delivery platform can attach without
redesigning orders. A `shipments` row is created when a seller ships (hangs off a
`seller_order`); a seller order may have one shipment covering its delivery.

| Column | Type | Notes |
|---|---|---|
| `id` | UUIDPK | |
| `seller_order_id` | UUID FK → seller_orders | which seller order this shipment belongs to |
| `carrier` | String(60), nullable | carrier name |
| `tracking_number` | String(255), nullable | carrier tracking reference |
| `status` | String enum | `shipped → delivered` |
| `shipped_at` / `delivered_at` | datetime, nullable | set on the corresponding transition |
| `notes` | Text, nullable | delivery notes |
| timestamps | mixin | |

`seller_order_id` and `status` are each indexed. Driven by the seller endpoints:
`POST /api/v1/orders/seller/{id}/ship` creates the shipment and moves the seller order to
`shipped`; `POST /api/v1/orders/seller/shipments/{shipment_id}/deliver` moves it to
`delivered`.

The seller's `delivered` = parcel handed to delivery. **Final receipt is the buyer's
call**: `POST /api/v1/orders/{order_id}/receive` confirms the buyer actually received the
order and sets `orders.completed_at`, closing the loop (idempotent). Buyers see each
seller's fulfillment status (and shipment) on their `GET /api/v1/orders/{order_id}`
response via the `fulfillment` field.

## 3. Status lifecycle (the carefully-designed part)

### Price / money invariants
- All gross values on `orders` / `order_items` are captured at **checkout time** from the
  listings (snapshots).
- MUHUZE commission split is **derived** at **`Paid`** time into `revenue_transactions`,
  using `PremiumService.get_commission_rate(seller_id)` → **7%** (active sub) or **12%**.

### State machines are separate — never one giant `orders.status`
```
orders.status        : pending | cancelled            (order lifecycle)
orders.payment_status: pending | paid | failed | refunded | partially_refunded  (owned by payments)
seller_orders.status : pending | accepted | shipped | delivered | rejected | cancelled
```

### Order lifecycle (`orders.status`)
```
pending ──(buyer cancels before payment)──▶ cancelled
```
Fulfillment/accept/ship/deliver transitions live in `seller_orders`, **not** on
`orders.status` — so money and fulfillment state machines evolve independently.

## 4. Exactly where commission is deducted (the money math)

At the **`Payment → paid`** step, in one DB transaction, in the payments service
(`mark_order_paid` / `create_seller_orders_for_order`):

1. Resolve: `PremiumService.get_commission_rate(seller_id)` → 7% or 12%.
2. For each seller in the order:
   ```
   commission_amount = round(seller_gross * revenue_rate / 100, 2)
   seller_earning    = round(seller_gross - commission_amount, 2)
   ```
3. Snapshot `revenue_rate` and the `commission_amount`/`seller_earning` onto the
   `revenue_transactions` row.
4. Create **one** revenue row per order (unique `order_id`) — never duplicated, even on a
   re-fired `paid`.
5. In the **same transaction**, `create_seller_orders_for_order` builds one `seller_orders`
   row per distinct seller in the order (fulfillment begins at payment, not checkout).

### Escrow: held → released

The money does **not** go straight to sellers. When it lands on MUHUZE's account at `paid`:

- `commission_amount` is **MUHUZE's to keep** from the start.
- `seller_earning` starts **`status = held`** — the remaining money MUHUZE will send the
  seller **only after the buyer confirms receipt**.

Release happens in `OrderService.receive` (`POST /orders/{id}/receive`), in the **same
transaction** that stamps `orders.completed_at`. `RevenueTransaction.release_for_order`
flips every still-held row for the order to `status = released` and stamps `released_at`.
It is idempotent — re-firing `receive` (or concurrent calls) can never double-release.

So the commission is always MUHUZE's revenue; the `seller_earning` is escrowed until the
buyer closes the loop.

Worked numbers to test (README principle: controlled accounts, known amounts):

| Seller gross | Rate | MUHUZE cut | Seller earning |
|---|---|---|---|
| 100.00 | 12% | 12.00 | 88.00 |
| 250.00 | 12% | 30.00 | 220.00 |
| 100.00 | 7% | 7.00 | 93.00 |

## 5. Backend flow (source of truth, per module)

1. **Cart** — `POST /carts/items` (add/update qty), `DELETE /carts/items/{id}`,
   `GET /carts` (buyer). References `seller_listings`.
2. **Checkout** (`POST /orders`, buyer) — validates cart + chosen address:
   - **stock + price are never taken from the client**: every line's listing is
     re-read from the DB; if `listing.stock < quantity` checkout rejects with
     `InsufficientStockError` (and unavailable listings raise
     `CartItemUnavailableError`) — no partial order is created;
   - snapshots `orders`, `order_items`, `shipping_infos`; prices snapshotted from
     the live listings;
   - clears the cart; returns order numbers per seller.
   - status `pending`, payment_status `pending`, `currency` `RWF`. **No commission math and no
     `seller_orders` yet** — those happen at payment time.
3. **Payment** — mobile money (Airtel Money) stub gateway:
   - `POST /payments` (`create`) → calls `StubMomoGateway.request_payment`, stores the returned
     `request_reference` as `provider_ref`; order stays `pending`.
   - `POST /payments/{id}/paid` (provider callback) → confirms via `confirm_payment`, then
     `mark_order_paid` runs `revenue_transactions` **and**
     `create_seller_orders_for_order` (per-seller `seller_orders`) in the **same DB
     transaction** (section 4) → order flips to `paid`.
4. **Fulfillment** — seller endpoints under `/api/v1/orders/seller` drive their own
   `seller_orders.status`: `GET ""` (list mine), `POST /{id}/accept`,
   `POST /{id}/reject` (with reason), `POST /{id}/ship` (creates a `shipments` row, moves to
   `shipped`). A seller only ever sees their own seller order + its items.
5. **Delivery** — `POST /shipments/{shipment_id}/deliver` moves the shipment (and its
   seller order) to `delivered`.
6. **Receipt** — `POST /orders/{order_id}/receive` (buyer) confirms the order was received
   and sets `orders.completed_at`. Buyer's `GET /orders/{id}` surfaces each seller's
   `fulfillment` (seller_order + shipment) so they can track accept → ship → deliver.

## 6. Build order (one financial flow at a time, per README)

Implemented — the core transaction:
1. `carts` + `cart_items`
2. `shipping_addresses`
3. `orders` + `order_items` + `shipping_infos` (checkout) — multi-seller via `order_items.seller_id`
4. `payments` (mobile money stub gateway, `airtel_money`)
5. `revenue` (`mark_order_paid`, commission split) + `seller_orders` created in the same transaction
6. `seller_orders` (per-seller fulfillment grouping, created at payment time) + `shipments` (delivery) + fulfillment/shipment endpoints
7. Buyer closes the loop: fulfillment visibility on `GET /orders/{id}` + `POST /orders/{id}/receive` (sets `completed_at`)

Deferred / future work: real PSP/Momo/MTN adapter swap-in (replacing the `StubMomoGateway`),
cancellation flows, buyer-side delivery disputes/dispatch exceptions, monitoring. Also still
deferred: wallets, withdrawals, referrals, refund/reversal engines, driver platform,
wishlist, favorites, reviews, recommendations, comparison, advanced promotions.

## 7. Decisions locked during implementation

1. **Multi-seller order policy** — one checkout across many sellers (a core MUHUZE
   differentiator). The model captures it on `order_items.seller_id`; the per-seller
   `seller_orders` fulfillment grouping is now implemented and created at payment time.
   Rejection/cancellation semantics (partial refunds) remain to be refined later.
2. **Address selection** — checkout requires choosing an existing `shipping_addresses` row
   (or entering one free-form that also creates a `shipping_infos` snapshot). Quick "new
   address" entry at checkout is available.
3. **Checkout reserved stock** — on order creation, listing stock is reserved/holds and
   finalized at `paid`.
4. **Commission per order vs per seller** — one `revenue_transactions` row per (order,
   seller), each seller paid separately since rates differ by seller (rather than a single
   order total).
5. **Dashboard/visibility** — admin visibility needs (all orders, all revenue) remain a
   future-work item.

## 8. Explicitly left out of this milestone (agreed)

Wishlist, favorites, product reviews, advanced recommendations, product comparison,
advanced promotions. The frontend's "cart screen" / "checkout screen" / "my orders"
concepts map onto the backend domain model above; we do **not** let those UI names drive
the schema.
