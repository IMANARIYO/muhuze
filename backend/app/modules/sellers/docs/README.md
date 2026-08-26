# Sellers Module

## Purpose

Owns the business relationship between an `Account` and MUHUZE as a
marketplace: applying to become a seller, submitting identity documents,
admin review, and the operational status (active/suspended/deactivated)
that everything else (products, orders, wallet — not built yet) will
eventually gate on.

## The one rule everything here follows

**Account is identity. Seller is a business role attached to that
identity. Never merge them.**

```
Account
   │  1 : 0..1
   ▼
Seller ──── 0..N ──── SellerDocument
```

- `Account` answers "who is this and can they log in" — unaffected by
  anything that happens to their `Seller` row. A suspended or rejected
  seller can still log in and buy things as a `buyer`.
- `Seller` answers "how does this account operate as a seller, and is that
  currently trusted" — see [lifecycle.md](lifecycle.md) for the full state
  machine.
- The `seller` **role** (RBAC, `auth` module) and `Seller.status` are
  deliberately two different things — see
  [lifecycle.md#role-vs-status](lifecycle.md#role-vs-status).

## Responsibilities

- Seller registration (`POST /sellers`) — a `Seller` row is at most one
  per account, ever; a rejected application is edited and resubmitted on
  the same row, never recreated.
- Profile editing, while editable (`PATCH /sellers/me`).
- Identity document upload/list/delete, Cloudinary-backed, private
  (`POST/GET/DELETE /sellers/me/documents...`) — see [documents.md](documents.md).
- Submission for review (`POST /sellers/me/submit`), with the
  required-documents check.
- Admin review: list/get/approve/reject/suspend/reactivate.
- Self-service deactivation.
- Email notifications at every lifecycle transition, via
  `app/core/notifications.py` (already built, reused here — see
  [../../auth/docs/README.md](../../auth/docs/README.md) for how that
  module treats email as a reusable core utility, same as here).

## Does Not Handle

- **Authentication, sessions, RBAC** — `auth`. This module only *reads*
  auth (`get_current_account`, `require_role("admin")`, granting the
  `seller` role on approval) — never manages accounts or roles directly.
- **Products, orders, wallet, revenue, withdrawals** — none of these
  modules exist yet. `Seller.status == ACTIVE` is the intended gate for
  all of them once they do (e.g. `require_active_seller`-style check —
  not built, since nothing consumes it yet).
- **Document version history / audit trail** — deliberately not built.
  Re-uploading a document type replaces it. See
  [documents.md](documents.md#deliberately-not-versioned).

## Architecture

Same 4-layer convention as every module, with one addition: `service.py`
holds two classes, not one — `SellerService` (lifecycle/state machine) and
`SellerDocumentService` (upload/replace/delete, Cloudinary-facing). They're
split because they change for different reasons and have different
failure modes (state transitions are pure DB logic; document handling has
to reason about a third-party service and partial-failure compensation —
see [documents.md](documents.md)).

## Endpoints

### Self-service

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/sellers` | Register — creates a `Seller` in `draft` status |
| GET | `/api/v1/sellers/me` | Own seller profile |
| PATCH | `/api/v1/sellers/me` | Edit profile — only while `draft` or `rejected` |
| POST | `/api/v1/sellers/me/submit` | Submit for review — requires identity documents present |
| POST | `/api/v1/sellers/me/deactivate` | Self-deactivate — only while `active` |
| POST | `/api/v1/sellers/me/documents` | Upload a document (multipart: `document_type` + `file`) — replaces an existing one of the same type |
| GET | `/api/v1/sellers/me/documents` | List own documents, each with a freshly-signed URL |
| DELETE | `/api/v1/sellers/me/documents/{document_id}` | Delete own document |

### Admin (`require_role("admin")`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/sellers?status=...` | List sellers, optionally filtered by status |
| GET | `/api/v1/sellers/{seller_id}` | Get one seller |
| GET | `/api/v1/sellers/{seller_id}/documents` | List a seller's documents (for review) |
| POST | `/api/v1/sellers/{seller_id}/approve` | `pending_review` → `active`, grants the `seller` role |
| POST | `/api/v1/sellers/{seller_id}/reject` | `pending_review` → `rejected` (body: `reason`) |
| POST | `/api/v1/sellers/{seller_id}/suspend` | `active` → `suspended` (body: optional `reason`) |
| POST | `/api/v1/sellers/{seller_id}/reactivate` | `suspended` → `active` |

Every transition endpoint enforces the state it requires and rejects with
`409` otherwise — see [lifecycle.md](lifecycle.md) for the full transition
table. Edge cases are documented inline in [lifecycle.md](lifecycle.md) and
[documents.md](documents.md), next to the behavior each one applies to,
rather than collected in a separate file.
