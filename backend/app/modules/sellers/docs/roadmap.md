# Sellers Roadmap

## Phase 1 — Core lifecycle

- [x] `Seller` model + migration (1:0..1 with `Account`, `SellerStatus` state machine)
- [x] `SellerRepository` — CRUD + one `mark_*` method per transition
- [x] `SellerService` — all state-transition guards, one specific exception per invalid transition
- [x] Registration (`POST /sellers`) — one row per account forever, duplicate business name rejected
- [x] Profile editing (`PATCH /sellers/me`) — only while `draft`/`rejected`
- [x] Submission (`POST /sellers/me/submit`) — required-documents check, email notification
- [x] Admin review: list (`GET /sellers?status=`), get, approve, reject (with reason), suspend (with optional reason), reactivate
- [x] Self-deactivation (`POST /sellers/me/deactivate`)
- [x] `seller` role granted on first approval, never auto-revoked by suspend/reject/deactivate — see `lifecycle.md#role-vs-status`
- [x] Email notification on every transition (submitted, approved, rejected, suspended, reactivated, deactivated), reusing `app/core/notifications.py`
- [x] Account never affected by seller status — verified directly: login still works after suspend/reject/deactivate

## Phase 2 — Documents

- [x] `SellerDocument` model + migration (Cloudinary-backed, private/authenticated delivery)
- [x] `SellerDocumentService` — upload/list/delete, reusing `app/core/storage.py`
- [x] Required-documents validation (any uploaded document is enough to submit)
- [x] Content-type + size validation before any network call
- [x] Re-upload replaces existing document of the same type (old Cloudinary asset deleted, best-effort)
- [x] Failure compensation: Cloudinary succeeds + DB fails → uploaded asset is cleaned up (tested by deliberately breaking the DB write)
- [x] Documents only editable while `draft`/`rejected` — same window as profile editing
- [x] Admin can list a seller's documents for review (`GET /sellers/{id}/documents`)
- [x] No public URLs stored or exposed — signed URLs computed per-request

## Verified (131 tests passing across the whole suite; sellers-specific: `test_sellers.py` + `test_seller_documents.py`)

- Full approval flow end-to-end, including role grant and account-unaffected checks
- Reject → edit → resubmit → approve
- Suspend → reactivate, with account login unaffected throughout
- Every wrong-state transition → `409` with a specific exception
- Duplicate registration, duplicate business name → `409`
- Missing required documents on submit → `422`
- Disallowed content type on upload → `400`
- Re-upload replace behavior + old-asset cleanup
- DB-write-fails-after-Cloudinary-succeeds compensation
- Cross-account document access blocked (can't delete someone else's document — `404`, not `403`, so as not to confirm the document exists)
- Non-admin blocked from every admin endpoint

## Not built — deliberate scope cuts, not oversights

- **Document version history / audit trail** — re-upload hard-replaces. See `documents.md#deliberately-not-versioned`.
- **"Reactivate from deactivated"** — only `suspended → active` exists. See `lifecycle.md#open-questions`.
- **Product/order/wallet gating on `Seller.status`** — nothing to gate yet; no such modules exist. The intended shape is documented in `lifecycle.md#role-vs-status`.
- **`require_active_seller`-style FastAPI dependency** — not built for the same reason; would be a thin wrapper once a module needs it.
- **Seller-specific permissions** (e.g. `products.create` scoped to own products) — the permission catalog is still empty platform-wide; not sellers-specific.
- **Business address fields** (country/province/district/etc.) — the original design discussion raised these but they were never locked down; `business_name` + `business_description` is what's actually needed today.
- **Malware/content scanning on uploaded documents** — only content-type/size are checked.
