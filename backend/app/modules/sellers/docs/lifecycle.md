# Seller Lifecycle

## States

`SellerStatus` (`app/modules/sellers/models.py`):

| Status | Meaning |
|---|---|
| `draft` | Application started, not yet submitted. Editable. Documents can be uploaded/replaced. |
| `pending_review` | Submitted, awaiting admin decision. **Not editable.** |
| `active` | Approved. Operational — this is the status future product/order/wallet gates will check. |
| `rejected` | Admin declined the application, with a `rejection_reason`. Editable again — see [resubmission](#resubmission-after-rejection). |
| `suspended` | Was `active`, admin has temporarily blocked seller operations. The **account** is unaffected — can still log in, still buy things. |
| `deactivated` | Seller voluntarily stopped operating (self-service, from `active` only). Reversible by the seller with one click — see [deactivation & reactivation](#deactivation--reactivation). |

## Transitions

```
                    register()
                        │
                        ▼
                     DRAFT ◄──────────────┐
                        │                 │
                submit_for_review()       │ update_profile()
                        │                 │ (edit while draft/rejected)
                        ▼                 │
               PENDING_REVIEW             │
                   │        │             │
              approve()  reject()         │
                   │        │             │
                   ▼        ▼             │
               ACTIVE   REJECTED ─────────┘
                 │  ▲
        suspend()│  │reactivate()
                 ▼  │
             SUSPENDED

ACTIVE ──deactivate()──► DEACTIVATED ──reactivate_mine()──► ACTIVE
```

Every arrow is enforced in `SellerService` by checking the *current*
status before mutating — attempting a transition from the wrong state
raises a specific `409` exception (`SellerNotSubmittableError`,
`SellerNotPendingReviewError`, `SellerNotActiveError`,
`SellerNotSuspendedError`, `SellerNotDeactivatedError`) rather than a
generic error, so a client can tell exactly what went wrong.

## Registration is one row, forever

A `Seller` row is created once per account and never recreated — enforced
by `Seller.account_id` being unique at the database level, and checked
again in `SellerService.register` (`SellerAlreadyExistsError`, 409) before
that constraint would even be hit. This is true even for a `rejected`
seller: they edit and resubmit the *same* row (see
[resubmission](#resubmission-after-rejection)), never register again.

## Resubmission after rejection

`rejected` is not a dead end. From `rejected`:

1. `PATCH /sellers/me` — edit business info (same as from `draft`).
2. Upload/replace documents as needed (same rules as `draft` — see
   [documents.md](documents.md)).
3. `POST /sellers/me/submit` — back to `pending_review`. `rejection_reason`
   is cleared on the next `submitted_at`/on approval, whichever comes
   first, so it never lingers as stale information once superseded.

## Deactivation & reactivation

`deactivated` is **not** a dead end for the seller:

1. `POST /sellers/me/deactivate` — voluntarily close the shop, `active` →
   `deactivated` (self-service).
2. `POST /sellers/me/reactivate` — re-open it with one click,
   `deactivated` → `active` (self-service).

This is intentionally distinct from the admin-only
`POST /sellers/{seller_id}/reactivate`, which handles `suspended` →
`active`. A `suspended` seller must go through an admin; a voluntarily
`deactivated` seller can re-open their own shop.

## Editability

Only `draft` and `rejected` allow `PATCH /sellers/me` and document
upload/replace. `pending_review`, `active`, `suspended`, `deactivated` are
all read-only for the seller — attempting to edit raises
`SellerNotEditableError` (409). This is deliberate: once submitted, the
information under review shouldn't change out from under the reviewer;
once active, changing verified business info would undermine the point of
having verified it.

## Role vs. status

**These are not the same thing, and conflating them is exactly the bug
this design avoids:**

- The `seller` **role** (RBAC — `auth` module) is granted once, on first
  `approve()`, and never revoked by anything in this module (not by
  reject, suspend, or deactivate — none of those are reachable from a
  state where the role would even have been granted yet, except suspend/
  deactivate which happen *after* approval and deliberately leave the role
  alone).
- `Seller.status` is the actual operational gate. An account can hold the
  `seller` role while `Seller.status == suspended` — meaning "this account
  has been a verified seller before" is still true, but "this account is
  currently allowed to sell" is false.

Future modules (products, orders) should gate on **`Seller.status ==
ACTIVE`**, not merely on `require_role("seller")`. Neither gate exists yet
— nothing has been built that needs it — but this is the intended shape
per the design discussion that produced this module, and per
`auth/docs/database.md`'s existing permission-vs-role guidance.

## Verified behaviors (see `tests/test_sellers.py`)

- Full happy path: register → upload documents → submit → admin approve
  → `seller` role granted → account can still log in.
- Reject → edit → resubmit → approve.
- Suspend an active seller → account can still log in → reactivate.
- Self-deactivate an active seller.
- Self-reactivate a deactivated seller back to active.
- Every wrong-state transition attempt returns `409`, not a generic error.
- Duplicate registration (409), duplicate business name (409).
- Submitting without required documents (422).

## Open questions

- **Business name uniqueness** is global and permanent (even a `draft`
  claims the name). Whether that's the right policy — vs. only reserving
  the name once `active` — hasn't been decided; kept simple for now.
