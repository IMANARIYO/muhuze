# Seller Plans, Subscriptions, and Commission API

**Status:** implemented (`app/modules/seller_plans/`). Rules and rationale: [`docs/features/017_seller_plans.md`](../features/017_seller_plans.md).

All paths are under `/api/v1` and use the [standard envelope](response-format.md). Money and rates are decimal strings: `"10000.00"` RWF, `"7.50"` percent.

## Plans

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/seller-plans` | – (public) | The plans on offer, cheapest first |
| GET | `/seller-plans/manage` | `seller_plan.manage` | Every plan, including retired. Filter: `status` |
| POST | `/seller-plans` | `seller_plan.manage` | Create a plan (201) |
| PATCH | `/seller-plans/{plan_id}` | `seller_plan.manage` | Change it (not its `code`) |
| POST | `/seller-plans/{plan_id}/retire` | `seller_plan.manage` | Stop offering it |
| POST | `/seller-plans/{plan_id}/reactivate` | `seller_plan.manage` | Offer it again |
| DELETE | `/seller-plans/{plan_id}` | `seller_plan.manage` | Delete a plan nobody ever subscribed to |

```json
{
  "code": "business",
  "name": "Business",
  "description": "For growing shops",
  "price": "30000",
  "duration_days": 30,
  "commission_rate": "4"
}
```

| Field | Rule |
|---|---|
| `code` | 2 to 50 lowercase letters, digits, underscores; unique; never changes |
| `name` | 1 to 100 characters |
| `description` | Optional, up to 1000 characters |
| `price` | 0 or more, at most two decimals. 0 is a free plan |
| `duration_days` | 1 to 3660 |
| `commission_rate` | 0 to 100, at most two decimals |

Editing a plan never changes a subscription that already exists.

## A seller's own subscriptions

Needs a login, the `seller_subscription.request` permission (every seller has it), and an **active** seller.

| Method | Path | Purpose |
|---|---|---|
| GET | `/seller-subscriptions/mine/terms` | The commission you are charged now, and why |
| GET | `/seller-subscriptions/mine` | Your subscription history, newest first |
| POST | `/seller-subscriptions/mine` | Request a plan (201). Body: `{ "plan_id": "…" }` |
| POST | `/seller-subscriptions/mine/{subscription_id}/withdraw` | Take back a pending request |

**Terms**

```json
{
  "commission_rate": "7.00",
  "source": "subscription",
  "subscription": { "…": "the subscription in force" },
  "upcoming": [ { "…": "an activated renewal that has not started" } ],
  "pending_request": null
}
```

`source` is `subscription`, `default`, or `not_set` (no plan, and MUHUZE has not set a default rate; `commission_rate` is then `null`).

**How a seller gets a plan today.** They request it, pay MUHUZE outside the app, and wait. The request is `pending` until staff activate it. Show the seller the plan's price and that it starts once payment is confirmed.

## Staff: subscriptions

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/seller-subscriptions` | `seller_subscription.manage` | Every subscription. `seller_id`, `plan_id`, `status`, `page`, `page_size`. The request queue is `status=pending` |
| POST | `/seller-subscriptions` | `seller_subscription.manage` | Assign a plan to a seller directly; active at once (201) |
| POST | `/seller-subscriptions/{id}/activate` | `seller_subscription.manage` | Activate a pending request |
| POST | `/seller-subscriptions/{id}/reject` | `seller_subscription.manage` | Decline a pending request. Body: `reason` |
| POST | `/seller-subscriptions/{id}/cancel` | `seller_subscription.manage` | End a running or scheduled subscription. Body: `reason` |

| Body | Fields |
|---|---|
| Assign | `seller_id`, `plan_id`, optional `payment_reference` |
| Activate | optional `payment_reference` (send `{}` if none) |
| Reject, cancel | `reason`, 5 to 500 characters, shown to the seller |

**When the new subscription starts**

| The seller already has | It starts |
|---|---|
| Nothing running or scheduled | Now |
| The **same plan** running or scheduled | When that one ends |
| A **different plan** | Now; the existing ones are cancelled with reason `Replaced by a new plan` |

**Subscription**

```json
{
  "id": "c1a2…",
  "seller_id": "3f0c…",
  "plan_id": "77de…",
  "plan_name": "Business",
  "price": "30000.00",
  "currency": "RWF",
  "duration_days": 30,
  "commission_rate": "4.00",
  "status": "active",
  "starts_at": "2026-10-07T10:00:00Z",
  "ends_at": "2026-11-06T10:00:00Z",
  "is_applicable": true,
  "status_reason": null,
  "payment_reference": "MOMO-778899",
  "decided_at": "2026-10-07T10:00:00Z",
  "created_at": "2026-10-07T09:30:00Z"
}
```

- `plan_name`, `price`, `duration_days`, `commission_rate` are what was agreed when the subscription was requested. They do not follow later edits to the plan.
- `status` is `pending`, `active`, `rejected`, or `cancelled`. There is no `expired`: use **`is_applicable`**, which is true only for the subscription in force right now. An `active` subscription with `is_applicable: false` has either ended or not started yet; compare `starts_at` and `ends_at` with the current time.

## Staff: the default commission rate

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `/commission-rates/default` | `default_commission_rate.manage` | The rate in force. `422` if none has been set |
| GET | `/commission-rates/default/history` | `default_commission_rate.manage` | Every rate ever set, newest first |
| POST | `/commission-rates/default` | `default_commission_rate.manage` | Set a rate (201) |

```json
{ "rate": "10", "effective_from": "2026-11-01T00:00:00+02:00", "note": "New year pricing" }
```

`effective_from` is optional (default: now), must carry a time zone, and cannot be in the past. `note` is optional, up to 500 characters. Setting a rate never edits an earlier one; it adds a row.

```json
{ "id": "…", "rate": "10.00", "effective_from": "…", "note": "…", "set_by_account_id": "…", "created_at": "…", "is_current": true }
```

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | Missing the permission |
| 403 | `Only an approved, active seller can do this` | The seller is suspended, closed, or not approved |
| 404 | `Plan not found` / `Subscription not found` / `Seller not found` | Unknown id, **another seller's subscription**, or a seller who is not active |
| 409 | `A plan with this code already exists` | Create |
| 409 | `Sellers have subscribed to this plan. Retire it instead of deleting it.` | Delete |
| 409 | `You already have a plan request waiting for a decision` | A second request |
| 409 | `Only a pending request can be activated` (or `rejected`, `withdrawn`) | Wrong status |
| 409 | `Only a running or scheduled subscription can be cancelled` | Cancel |
| 409 | `This seller already has a subscription for that period. Please try again.` | Two changes collided |
| 409 | `A rate is already set to take effect at that exact moment` | Default rate |
| 422 | `This plan is no longer offered` | Requesting or assigning a retired plan |
| 422 | `MUHUZE has not set its commission rate yet` | Reading the default rate before one exists |
| 422 | `The rate can only take effect now or in the future` | Backdating |
| 422 | field errors | Request validation |
