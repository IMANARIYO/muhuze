# 019 — Services and service requests

**Status:** `TESTING`.

Business rules: [`README.md` §7.5](../../../README.md#75-services-and-service-providers) and §20 (`X1`, `X2`, `X3` in part, `V1`–`V8`, `V10`, `V11`, `V13`). API contract: [`docs/api/service_requests.md`](../api/service_requests.md), plus the `kind` additions in [`products.md`](../api/products.md) and [`orders.md`](../api/orders.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml) (migration `0011`).

## Purpose

Let a shop offer **services** (cleaning, tutoring, repairs, …) besides goods, and let a buyer get one the way the README decided: **request → the provider accepts → the buyer pays**. A service provider is an ordinary seller, a business or an independent individual, approved through the same application (`V1`). Nothing about wallets, commission, or withdrawals is new: an accepted request becomes an ordinary order.

## Scope

| In this feature | Not in this feature |
|---|---|
| `kind` on listings (`product` / `service`), fixed at creation | Rentals (`X1`: out of scope) |
| Checkout refuses services | Provider calendars or time slots (`V7`: the buyer proposes a time) |
| Service requests: request, cancel, accept, decline, staff view | Automatic expiry of unanswered or unpaid requests (`V8`: none) |
| Service orders: `kind`, `scheduled_for`, the shorter path after payment | Dispute handling (`V13`: staff, by hand) |
| The provider's phone on a service, by subscription | Licence checks for some services (`V9`, open) |
| | Phone rules for product sellers, admin require/exempt (`V11`: services only, none) |

## How it works

```
Buyer                         Provider (active seller)            Orders / payments / wallets
  │ POST /service-requests       │
  │   status: requested ────────►│ GET /service-requests/incoming
  │                              │
  │◄── declined (reason) ────────┤ POST …/decline
  │                              │
  │◄── accepted ─────────────────┤ POST …/accept ──► create_service_order()
  │       order: awaiting_payment                      Order kind=service, one SellerOrder,
  │                                                    one item at the REQUESTED price,
  │                                                    commission terms resolved NOW
  │ pays the order (payments API) ─────────────────► mark_paid → SellerOrder: accepted
  │                                                              earning: pending
  │                              │ POST /seller-orders/mine/{id}/mark-done → delivered
  │ confirm-receipt ───────────────────────────────► completed → earning: available
  │                              │ (or reject with reason → earning reversed, refund owed)
```

## Rules

**Decided 2026-10-22** (README §7.5, §20):

1. **A listing is a product or a service** (`products.kind`). It is chosen at creation and never changes, because checkout and requests depend on it. Services use the same categories, attributes, pictures, publishing, and staff hiding as goods.
2. **The storefront lists goods by default.** `GET /products` returns `kind=product` unless `kind=service` is asked for, so a client that only knows checkout never offers a service by mistake. Sellers and staff see both kinds unless they filter.
3. **A service is never checked out** (`V2`). Checkout fails with `422` and names the services; nothing is ordered.
4. **A request is for one service from one provider**, at a time the buyer proposes (in the future, with a time zone), with a contact name and phone and an optional note (`V7`). There is no calendar and no clash check.
4a. **The request must fit the service's details** (`V15`–`V18`, decided 2026-10-24): a `place` (province, district, sector, optional address) only for a service done at the buyer's place, and then in one of the districts it covers (any case); no place for `at_provider` or `online`. The time must be at least `min_notice_hours` ahead and start within that weekday's working hours, in Rwanda time (`SERVICE_TIMEZONE`). These are checked when the request is sent, by `_check_place` and `_check_time` in the service; a later change to the listing does not affect a request already sent. A service published before details existed takes no requests (`404`) until its seller completes it.
5. **The price is fixed** (`V5`): the listing's price, recorded on the request. The order created on acceptance charges exactly that price, even if the provider has changed the listing since.
6. **Nothing is paid before acceptance.** The buyer can cancel while the request is `requested`. The provider accepts or declines; declining needs a reason the buyer sees. Each request is answered once.
7. **Accepting needs** an active provider, the request still `requested`, its time still in the future, and the service still on offer (published, not hidden by staff, category on). It creates the order in the same transaction; `service_requests.order_id` is unique, so one request never makes two orders.
8. **After acceptance it is an ordinary order** (`orders.kind = service`, `scheduled_for` set). Payment confirmation releases it straight to `accepted` (no second accept). The provider marks it **done** (stored as `delivered`; there is no `shipped`), and the buyer confirms, which completes it and **settles the earning** (`V4`, `W1`). Commission comes from the same resolver and default rate as goods (`V3`).
9. **A provider who cannot do a paid service** rejects it with a reason (`accepted` → `rejected`): the pending earning is reversed and the buyer is owed a refund, which is manual (`R1`).
10. **An accepted request does not expire**, and neither does its unpaid order (`V8`, as `P3`): the buyer cancels the order if they change their mind.
11. **The provider's phone** (`business_phone`) is in the public page of a **service** only while the provider has **any subscription in force** (`V10`). Otherwise `contact_phone` is `null`, withheld by the API. Product listings never show it (`V11`). The rule lives in one place: `ProductService._contact_phone`, which asks `SellerPlanService.has_subscription_in_force`.
12. **Once a service order is paid, its buyer sees the provider's phone** (`provider_phone` on the order's seller order), with or without a subscription (`V14`). Never before payment, never on goods. The rule lives in one place: `OrderService._provider_phones`, which reads the phone through `SellerService.get_business_phones`.
13. **"It was not done"** (`V13`): there is no dispute flow. The earning stays pending until the buyer confirms, and staff handle complaints by hand.

**Ownership.** A buyer reaches only their own requests; a provider only requests to their own shop. Anything else is `404`, for reads and writes alike.

**Concurrency.** Cancel, accept, and decline lock the request row first, so a buyer's cancel and a provider's accept can never both succeed.

## Who sees what

| Who | Sees |
|---|---|
| Buyer | Their own requests, and the order once accepted |
| Provider | Requests to their shop, including the buyer's contact for the job (`service_request.manage`) |
| Staff with `service_request.read` | Every request |

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `service_request.manage` | See and answer the requests sent to your own shop | `seller` |
| `service_request.read` | See every service request | – |

## Design

- **No separate services table.** A service is a `products` row with `kind = service`, so attributes, pictures, moderation, and publishing are not duplicated. `service_requests` holds only what happens before there is an order.
- **Orders own everything after acceptance.** `OrderService.create_service_order` (no commit; the request's transaction) builds the order with the same helpers as checkout (`_new_order`, `_new_seller_order`, `_order_item`), so the commission snapshot and split are computed by the same code.
- **Kind-aware seller steps.** `OrderService._seller_step` takes the allowed starting statuses per order kind; a step missing for a kind is refused with `409`.
- **Cross-feature calls** go through services only: requests → `ProductService.get_public_product`, `OrderService.create_service_order` / `get_order_summaries`, `SellerService.find_seller_id`; products → `SellerPlanService.has_subscription_in_force`.

## Database (migrations 0011, 0012)

- `products.kind` (`product` | `service`, default `product`; every existing listing is goods).
- `orders.kind` (default `product`) and `orders.scheduled_for`, with the check `(kind = 'service') = (scheduled_for IS NOT NULL)`.
- `service_requests`: the snapshot (service name, shop name, price, currency), when and where, status and answer, and `order_id` (unique). Check: `(status = 'accepted') = (order_id IS NOT NULL)`.
- `0012`: `products.service_location`, `service_duration_minutes`, `service_min_notice_hours`; tables `product_service_areas` and `product_service_hours`; `orders.service_location` and a nullable place; `service_requests.service_location` and a nullable place. Existing service orders and requests are backfilled as `at_customer` (they all had the buyer's place). Services published before `0012` have no details and take no requests until completed.

## Tests

`tests/api/service_requests/test_service_request_routes.py` (27 tests): listing kind and storefront filter, service details required to publish, the place / district / notice / working-hours checks on a request, `at_provider` and `online` services, the district filter, checkout refusal, the phone rule with and without a subscription, the provider's phone (and, at the provider's place, address) on a paid service order only, request validation, accept at the requested price with the persisted commission split, decline, cancel, accepting too late or after the listing is hidden, the full paid → done → confirmed → settled path, provider cancellation reversing the earning, ownership and permissions, and the database check on accepted requests.

Run the whole suite (README / CLAUDE.md: the user runs it):

    cd backend && .venv/Scripts/python -m pytest -q

## Progress

- [x] Rules decided and written into README §7.5 / §20
- [x] Database design (DBML) and migration 0011
- [x] Service details (`V15`–`V18`): migration 0012, products, orders, requests, docs, tests
- [x] Products: `kind`, filters, `contact_phone`
- [x] Orders: refuse services at checkout, `create_service_order`, `mark-done`, kind-aware steps
- [x] Service requests module: routes, service, repository, schemas, permissions
- [x] API docs
- [x] Tests written
- [ ] Tests run and passing (user)
- [ ] Walk-through against a real database
