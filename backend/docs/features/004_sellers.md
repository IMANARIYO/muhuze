# 004 — Sellers

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §15](../../../README.md#15-seller-verification-gates-withdrawals). API contract: [`docs/api/sellers.md`](../api/sellers.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Let an account apply to become a seller, and let staff verify that application **before** the seller can trade. Products, orders, wallets, and withdrawals will all hang off the seller record created here.

## Scope

| In this feature | Not in this feature |
|---|---|
| The seller application: business info, identity, location | Products, orders, earnings → later features |
| Private upload of identity and business documents | Public shop page for buyers → with products |
| Submit, approve, reject (with reason), resubmit | Email notifications of decisions → `014_notifications` |
| Suspend / reinstate (staff), close / reopen (seller) | Seller plans and subscriptions → their own feature |
| Staff list with filter, search, sort; status history | Phone number verification by SMS |
| Private file storage (Cloudinary) | Payout destinations → withdrawals |

## Lifecycle

```
            apply
              │
              ▼
            DRAFT ◄──────────────────┐
              │ submit               │ edit + re-upload
              ▼                      │
        PENDING_REVIEW ──reject──► REJECTED
              │ approve
              ▼
            ACTIVE ◄──reinstate── SUSPENDED      (staff)
              │  ▲ └──suspend────────►
   deactivate │  │ reactivate
              ▼  │
          DEACTIVATED                            (the seller)
```

| Status | Meaning | Can the seller edit? |
|---|---|---|
| `draft` | Started, not sent | Yes |
| `pending_review` | Sent, waiting for staff | No |
| `active` | Approved. **The only status that may list products, sell, or withdraw** | No |
| `rejected` | Declined with a reason | Yes, then submit again |
| `suspended` | Blocked by staff, with a reason | No |
| `deactivated` | Closed by the seller, who can reopen it | No |

## Rules

**The application**

- An account has **at most one** seller record, forever. A rejected seller fixes and resubmits the same record; it is never deleted.
- **Business name** is unique whatever the letter case (`Amina Fashion` = `AMINA fashion`).
- **Identity:** one document type (national ID, passport, driving license) and its number. The number is returned only to the owner and to staff with `seller.read`, and is never logged.
- **Location:** exactly one. Province, district, and sector are required; cell, village, and street address are optional. **GPS coordinates are optional**: when sent, latitude and longitude come together with a `source` (`device` = detected, `manual` = a pin). They are stored to six decimal places.
- The application can be changed **only while `draft` or `rejected`**.

**Documents**

- JPEG, PNG, or PDF, up to **5 MB**. The type is decided from the file's first bytes, not from its name or what the client claims.
- **Required to submit:** `identity_front`, and `identity_back` unless the identity document is a passport.
- **Optional:** `business_registration`, `tin_certificate`. A seller without a registered business can still apply. No selfie is collected.
- One file per document type; uploading again replaces it and removes the old file.
- **Stored privately.** There is no public link, and the application response never contains a link or a storage id. A link is created per request, works for **5 minutes**, and is given only to the owner or to staff with `seller.read`.

**Review**

- Only a `pending_review` application can be approved or rejected.
- **Approve:** the seller becomes `active` and the account receives the `seller` role, in one transaction. `approved_at` records the *first* approval and is never cleared.
- **Reject:** needs a reason (5 to 500 characters) that the seller sees.
- **Staff cannot review their own application.**
- The `seller` role means "was approved once". It is not removed by suspension or deactivation. Whether a seller may trade *now* is the **status**, which is why other features must ask `SellerService.get_active_seller()` and not check the role.

**Suspension and closing**

- Staff can suspend an `active` seller with a reason, and reinstate them. A suspended seller cannot lift it themselves.
- A seller can close (`deactivated`) and reopen their own `active` shop.
- **Seller status never affects the account:** a suspended or closed seller can still log in and buy.

**History**

- Every status change is recorded with who made it, when, and why (`seller_status_history`, append-only).
- The reason on the seller is the reason for its *current* status; it is cleared when the seller moves on. Past reasons stay in the history.

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `seller.read` | See every seller, their identity details, documents, and history | – |
| `seller.review` | Approve or reject a waiting application | – |
| `seller.suspend` | Suspend an active seller; reinstate a suspended one | – |

Only `admin` holds these until an admin assigns them to another role (for example a `support` role with `seller.read` and `seller.review`).

A seller managing **their own** application needs only a login: the `/sellers/me` endpoints always act on the caller's own record, so there is nothing to grant.

## Design

```
app/modules/sellers/
├── seller_routes.py        # /sellers/me (own) and /sellers (staff)
├── seller_dependencies.py
├── seller_service.py       # every rule above; the get_active_seller gate
├── seller_repository.py    # queries, list filter/search/sort
├── seller_mapper.py        # flat location columns → nested API object
├── seller_model.py         # Seller, SellerDocument, SellerStatusHistory
├── seller_schema.py
├── seller_permissions.py
├── seller_exceptions.py
└── seller_constants.py     # statuses, document types, limits
```

| Supporting file | Role |
|---|---|
| `app/infrastructure/storage/file_storage.py` | `FileStorage` interface, Cloudinary adapter (private "authenticated" assets, signed expiring links), and a stand-in that fails clearly when no credentials are set |
| `migrations/versions/…0003…` | The three tables |

**For other features.** To check that the caller may sell, call `SellerService.get_active_seller(account_id)`. It returns the seller or raises `403`. This is the single place that rule lives (README §5.3).

**Concurrency.** A seller row is locked (`FOR UPDATE`) for every edit and status change, so two staff members cannot approve and reject the same application at once.

**Files and the database.** A file is uploaded first, then its row is saved. When a file is replaced or removed, the old file is deleted from storage after the commit. If that deletion fails it is logged and the request still succeeds: the database is correct, and the cost is one orphaned private file.

**List endpoint** (`GET /sellers`): filter `status`; search `q` in the business name (contains, case-insensitive, up to 100 characters, `%` and `_` are literal); sort by `created_at`, `submitted_at`, or `business_name`, with `-` for descending. All done in SQL.

## Configuration

`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` (all three or none). Without them the application itself works, but uploading a document returns `503`.

## Security review

- [x] Staff endpoints need a specific permission, even for the caller's own seller record (tested for all 8).
- [x] `/sellers/me` can only ever reach the caller's own record: the account comes from the token, never from the request.
- [x] Documents are private; links are signed, expire in 5 minutes, and are never stored or returned in bulk.
- [x] File type is verified from content; size is capped, and the server reads at most 5 MB + 1 byte.
- [x] The identity number is absent from the staff list and from every log line.
- [x] Sort and filter values are an allowlist; search input is escaped.
- [x] Staff cannot approve or reject their own application.
- [x] Approval and the `seller` role are one transaction.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| The seller is not notified by email when approved, rejected, or suspended | They must open the app to find out | `014_notifications` |
| A seller's row is locked while a document uploads | A slow upload delays other actions on that same seller only | Acceptable; revisit if uploads become large |
| Uploaded files are not scanned for malware | A malicious PDF could be opened by a reviewer | Decide before launch |
| The business phone is not verified | A wrong number goes unnoticed | Phone verification (needs an SMS provider) |
| Whether a suspended or deactivated seller can withdraw existing earnings | Undecided: README §20 `S2` | Withdrawals |
| An approved seller cannot change business details | They would need staff help | Decide: edit with re-review, or staff-only edits |

## Progress

- [x] Requirements and rules (this document, README §15, decisions `S1`, `S3`–`S7`)
- [x] Database design and migration `0003` (applied to the development database)
- [x] File storage adapter
- [x] Models, repository, service, schemas, routes, permissions
- [x] Tests written: `tests/api/sellers/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [ ] **A real upload to Cloudinary** (needs the `CLOUDINARY_*` values; so far only exercised with a stand-in storage)
