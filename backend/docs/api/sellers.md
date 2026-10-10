# Sellers API

**Status:** implemented (`app/modules/sellers/`). Rules and rationale: [`docs/features/004_sellers.md`](../features/004_sellers.md).

All paths are under `/api/v1/sellers`. Every endpoint needs `Authorization: Bearer <access token>` and uses the [standard envelope](response-format.md).

## How a seller applies

```
POST /me                          start the application (status: draft)
PUT  /me/documents/identity_front upload each document
PUT  /me/documents/identity_back
POST /me/submit                   send for review (status: pending_review)
GET  /me                          check the status and, if rejected, the reason
```

While `draft` or `rejected`, the application can be edited (`PATCH /me`) and documents replaced. `missing_documents` in the response says what is still needed; `submit` works once it is empty.

## The caller's own application

| Method | Path | Purpose |
|---|---|---|
| POST | `/me` | Start an application (201). `409` if one exists |
| GET | `/me` | The application, status, and documents. `404` if none |
| PATCH | `/me` | Change it. Only the fields sent are changed; `location` is replaced whole |
| PUT | `/me/documents/{document_type}` | Upload or replace a document: multipart form, field `file` |
| DELETE | `/me/documents/{document_type}` | Remove a document |
| GET | `/me/documents/{document_type}/url` | A private link to the document, valid 5 minutes |
| POST | `/me/submit` | Send for review |
| POST | `/me/deactivate` | Close your own shop (`active` → `deactivated`) |
| POST | `/me/reactivate` | Reopen it (`deactivated` → `active`) |

`document_type`: `identity_front`, `identity_back` (required, except `identity_back` for a passport), `business_registration`, `tin_certificate` (optional). Files: JPEG, PNG, or PDF, up to 5 MB.

## Staff

| Method | Path | Needs | Purpose |
|---|---|---|---|
| GET | `` (list) | `seller.read` | All sellers. `status`, `q`, `sort`, `page`, `page_size` |
| GET | `/{seller_id}` | `seller.read` | Full application, including identity details |
| GET | `/{seller_id}/documents/{document_type}/url` | `seller.read` | A private link to a document, valid 5 minutes |
| GET | `/{seller_id}/history` | `seller.read` | Every status change, newest first |
| POST | `/{seller_id}/approve` | `seller.review` | `pending_review` → `active`; grants the `seller` role |
| POST | `/{seller_id}/reject` | `seller.review` | `pending_review` → `rejected`. Body: `reason` |
| POST | `/{seller_id}/suspend` | `seller.suspend` | `active` → `suspended`. Body: `reason` |
| POST | `/{seller_id}/reinstate` | `seller.suspend` | `suspended` → `active` |

**List parameters**

| Parameter | Values |
|---|---|
| `status` | `draft`, `pending_review`, `active`, `rejected`, `suspended`, `deactivated`. The review queue is `status=pending_review` |
| `q` | Searches the business name: contains, case-insensitive, 1 to 100 characters |
| `sort` | `created_at`, `submitted_at`, `business_name`; prefix `-` for descending. Default `-created_at` |

## Bodies

**Apply** (`POST /me`); `PATCH /me` takes any subset:

```json
{
  "business_name": "Amina Fashion",
  "business_description": "Clothes and shoes",
  "business_phone": "+250788123456",
  "identity_document_type": "national_id",
  "identity_document_number": "1199080012345678",
  "location": {
    "province": "Kigali",
    "district": "Gasabo",
    "sector": "Remera",
    "cell": "Rukiri I",
    "village": null,
    "street_address": "KG 11 Ave, near the stadium",
    "latitude": -1.953571,
    "longitude": 30.112735,
    "accuracy_m": 12,
    "source": "device"
  }
}
```

| Field | Rule |
|---|---|
| `business_name` | 2 to 150 characters; unique, ignoring letter case |
| `business_description` | Optional, up to 2000 characters |
| `business_phone` | E.164, e.g. `+2507XXXXXXXX` |
| `identity_document_type` | `national_id`, `passport`, `driving_license` |
| `identity_document_number` | 3 to 50 characters |
| `location.province`, `district`, `sector` | Required |
| `location.cell`, `village`, `street_address` | Optional |
| `location.country_code` | Optional, ISO two letters, default `RW` |
| `location.latitude`, `longitude` | Optional, but sent together, with `source` |
| `location.source` | `device` (detected by the phone or browser) or `manual` (a pin) |
| `location.accuracy_m` | Optional; the accuracy the device reported, in metres |

**Detecting the location (frontend).** Use the browser's `navigator.geolocation.getCurrentPosition`, and send `coords.latitude`, `coords.longitude`, `Math.round(coords.accuracy)` as `accuracy_m`, and `"source": "device"`. If the user refuses or it fails, send the address without coordinates, or let them place a pin and send `"source": "manual"`.

**Reject / suspend:** `{ "reason": "The ID photo is too blurry to read" }` (5 to 500 characters; shown to the seller).

## Responses

**Seller** (own application and staff detail):

```json
{
  "id": "3f0c…",
  "account_id": "9a1b…",
  "business_name": "Amina Fashion",
  "business_description": "Clothes and shoes",
  "business_phone": "+250788123456",
  "identity_document_type": "national_id",
  "identity_document_number": "1199080012345678",
  "location": { "country_code": "RW", "province": "Kigali", "…": "…" },
  "status": "rejected",
  "status_reason": "The ID photo is too blurry to read",
  "submitted_at": "2026-10-06T12:00:00Z",
  "reviewed_by_account_id": "c77d…",
  "reviewed_at": "2026-10-06T13:10:00Z",
  "approved_at": null,
  "created_at": "2026-10-06T11:40:00Z",
  "documents": [
    { "document_type": "identity_front", "original_filename": "id.jpg", "mime_type": "image/jpeg", "file_size": 482113, "uploaded_at": "2026-10-06T11:45:00Z" }
  ],
  "missing_documents": ["identity_back"]
}
```

Documents carry no link. Ask for one when the user opens a document: `{ "url": "https://…", "expires_in": 300 }`. Do not store the link.

**List item:** `id`, `account_id`, `business_name`, `business_phone`, `district`, `status`, `submitted_at`, `created_at`. No identity details.

**History item:** `from_status`, `to_status`, `reason`, `changed_by_account_id`, `created_at`.

## Errors

| Status | Message | When |
|---|---|---|
| 401 | `Authentication required` | No valid access token |
| 403 | `You do not have permission to perform this action` | Staff endpoint without the permission |
| 404 | `You have not applied to become a seller` | `/me` endpoints before applying |
| 404 | `Seller not found` / `Document not found` | Unknown id, or that document was not uploaded |
| 409 | `You already have a seller application` | Applying twice |
| 409 | `This business name is already taken` | Apply or update |
| 409 | `The application can only be changed while it is a draft or after a rejection` | Editing or uploading in any other status |
| 409 | status-specific message, e.g. `Only an active seller can be suspended` | A status change that isn't allowed from the current status |
| 422 | `Upload these documents before submitting: identity_back` | Submitting with required documents missing |
| 422 | `The file must be a JPEG, PNG, or PDF` / `The file is larger than 5 MB` | Upload |
| 422 | `You cannot review your own seller application` | Approve or reject |
| 422 | field errors | Request validation |
| 503 | `File storage is not available right now. Please try again later.` | Storage is not configured or not reachable |
