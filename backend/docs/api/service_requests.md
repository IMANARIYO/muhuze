# Service requests API

**Status:** implemented (`app/modules/service_requests/`). Rules and rationale: [`docs/features/019_service_requests.md`](../features/019_service_requests.md), README §7.5.

All paths are under `/api/v1/service-requests`, need `Authorization: Bearer <access token>`, and use the [standard envelope](response-format.md). Money is a decimal string in RWF.

## How a service is bought

```
1. Buyer     POST /service-requests                       status: requested     (nothing to pay)
2. Provider  POST /service-requests/incoming/{id}/accept  status: accepted      → `order` is set
             (or …/decline with a reason                  status: declined)
3. Buyer     pays `order.id` like any order               → payments API
4. Provider  POST /seller-orders/mine/{seller_order_id}/mark-done              → orders API
5. Buyer     POST /orders/mine/{order_id}/seller-orders/{seller_order_id}/confirm-receipt
                                                          → the provider's earning becomes available
```

Find services to request with `GET /products?kind=service` ([products API](products.md)). A service is never put in the cart: checkout refuses it.

## For the buyer

Needs a login only. Every path reaches only the caller's own requests.

| Method | Path | Purpose |
|---|---|---|
| POST | `` | Request a service (201) |
| GET | `/mine` | Your requests, newest first. `status`, `page`, `page_size` |
| GET | `/mine/{request_id}` | One request. Once accepted, `order` is the order to pay |
| POST | `/mine/{request_id}/cancel` | Withdraw it while still `requested`. Body: `{}` or `{ "reason": "…" }` |

**Request a service**

```json
{
  "service_id": "b7e2…",
  "scheduled_for": "2026-11-02T09:00:00+02:00",
  "location": {
    "recipient_name": "Carol Mukamana",
    "recipient_phone": "+250788999000",
    "province": "Kigali",
    "district": "Kicukiro",
    "sector": "Niboye",
    "address": "KK 15 Ave, house 12"
  },
  "note": "Two bedrooms"
}
```

| Field | Rule |
|---|---|
| `service_id` | A listing on offer with `kind: "service"` |
| `scheduled_for` | With a time zone, and in the future |
| `location.recipient_name`, `recipient_phone` | Whom the provider contacts. Phone in E.164 |
| `location.province`, `district`, `sector` | Required |
| `location.address` | Optional, up to 255 characters |
| `note` | Optional, up to 500 characters; the provider sees it |

**Do not send a price.** The backend reads it from the listing and records it: if the provider later changes the price, this request is still charged what the buyer saw.

**After acceptance**, the request is answered and does not change again. To back out of an accepted request that is not paid yet, cancel its order: `POST /orders/mine/{order.id}/cancel`.

## For the provider

Needs a login, the `service_request.manage` permission (every seller has it), and an **active** seller. A provider sees only requests sent to their own shop.

| Method | Path | Purpose |
|---|---|---|
| GET | `/incoming` | Requests to your shop, newest first. New work is `status=requested` |
| GET | `/incoming/{request_id}` | One request: what, when, where, whom to contact |
| POST | `/incoming/{request_id}/accept` | `requested` → `accepted`; creates the order for the buyer to pay |
| POST | `/incoming/{request_id}/decline` | `requested` → `declined`. Body: `{ "reason": "…" }` (5 to 500 characters; the buyer sees it) |

Accepting needs the service to be **on offer right now** (published, not hidden by staff) and the requested time to be **still in the future**. Once the buyer pays, the order appears in `GET /seller-orders/mine` with `kind: "service"` and status `accepted`.

## For staff

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `` | `service_request.read` | Every request. `status`, `seller_id`, `buyer_account_id`, `page`, `page_size` |
| GET | `/{request_id}` | `service_request.read` | Any request |

## Response

The same shape for the buyer, the provider, and staff:

```json
{
  "id": "4a10…",
  "status": "accepted",
  "status_reason": null,
  "service_id": "b7e2…",
  "service_name": "Home cleaning",
  "seller_id": "3f0c…",
  "seller_name": "Pat Cleaning",
  "buyer_account_id": "91d2…",
  "unit_price": "20000.00",
  "currency": "RWF",
  "scheduled_for": "2026-11-02T07:00:00Z",
  "location": { "recipient_name": "Carol Mukamana", "recipient_phone": "+250788999000", "province": "Kigali", "district": "Kicukiro", "sector": "Niboye", "address": "KK 15 Ave, house 12", "note": "Two bedrooms" },
  "responded_at": "2026-10-22T10:05:00Z",
  "cancelled_at": null,
  "created_at": "2026-10-22T09:50:00Z",
  "order": {
    "id": "0c9d…",
    "order_number": "MHZ-000124",
    "kind": "service",
    "scheduled_for": "2026-11-02T07:00:00Z",
    "status": "awaiting_payment",
    "currency": "RWF",
    "total_amount": "20000.00",
    "paid_at": null,
    "cancelled_at": null,
    "created_at": "2026-10-22T10:05:00Z"
  }
}
```

| `status` | Meaning |
|---|---|
| `requested` | Waiting for the provider. The buyer can still cancel |
| `accepted` | The provider agreed. Follow `order.status` from here |
| `declined` | The provider said no; `status_reason` says why |
| `cancelled` | The buyer withdrew it |

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | Provider or staff endpoint without the permission |
| 403 | `Only an approved, active seller can do this` | The provider is suspended, closed, or not approved |
| 404 | `Service not found` | Unknown id, or the service is not on offer right now |
| 404 | `Service request not found` | Unknown id, **someone else's request**, or another shop's |
| 409 | `Only a request still waiting for an answer can be accepted` (and the like) | Answering or cancelling twice, or after the other side acted |
| 422 | `This listing is a product. Add it to your cart and check out instead.` | `service_id` is goods |
| 422 | `You cannot request a service from your own shop` | |
| 422 | `The time for the service must be in the future` | `scheduled_for` has passed (or has no time zone: field error) |
| 422 | `The requested time has passed. The buyer can send a new request.` | Accepting too late |
| 422 | `This service is not on offer right now. Publish it again to accept the request.` | Accepting while the listing is archived or hidden |
| 422 | `MUHUZE has not set its commission rate yet` | Accepting before staff set the default rate |
| 422 | field errors | Request validation |
