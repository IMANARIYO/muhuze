# Sellers Database

Conventions (UUID PK, timestamp mixin, table naming) are shared across all
modules — see [`auth/docs/database.md`](../../auth/docs/database.md#conventions-used-throughout).

## `sellers`

Table: `sellers` · Model: `app/modules/sellers/models.py::Seller`

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| account_id | UUID | No | FK → `accounts.id`. **Unique** — enforces 1:0..1 with `Account`. |
| business_name | VARCHAR(150) | No | Unique, indexed. |
| business_description | TEXT | Yes | |
| status | VARCHAR(20) | No | Indexed. One of `SellerStatus` — see [lifecycle.md](lifecycle.md). |
| rejection_reason | TEXT | Yes | Set on rejection, cleared on the next submission or approval. |
| submitted_at | TIMESTAMPTZ | Yes | Set when the seller submits for review. |
| reviewed_by | UUID | Yes | FK → `accounts.id` — the admin who approved/rejected. |
| reviewed_at | TIMESTAMPTZ | Yes | |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Never hard-deleted.** Once a seller has orders/revenue/wallet history
(future modules), deleting the row would destroy financial history. The
lifecycle is always a `status` transition — see
[lifecycle.md](lifecycle.md) — never a `DELETE`. This is a deliberate
constraint carried into the code, not just a convention: there is no
`delete_seller` anywhere in the repository or service.

## `seller_documents`

Table: `seller_documents` · Model: `app/modules/sellers/models.py::SellerDocument`

| Column | Type | Nullable | Description |
|---|---|---:|---|
| id | UUID | No | Primary key |
| seller_id | UUID | No | FK → `sellers.id`, `ondelete="CASCADE"`. Indexed. |
| document_type | VARCHAR(30) | No | One of `SellerDocumentType` (`national_id_front`, `national_id_back`, `passport`, `driving_license`). Indexed. |
| cloudinary_public_id | VARCHAR(255) | No | Cloudinary's identifier — needed to delete or re-sign access. |
| cloudinary_resource_type | VARCHAR(20) | No | Cloudinary's `resource_type` (`image`, `raw`, ...) — needed for delete/sign calls to target the right asset. |
| original_filename | VARCHAR(255) | Yes | As uploaded by the client — display only, never trusted for content-type/validation decisions. |
| mime_type | VARCHAR(100) | No | |
| file_size | INTEGER | No | Bytes. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Unique on `(seller_id, document_type)`** — at most one row per document
type per seller. Re-uploading the same type replaces the row (and deletes
the old Cloudinary asset) rather than keeping history. See
[documents.md](documents.md#deliberately-not-versioned) for why, and for
the upload/replace/failure-compensation design in full.

**No public URL is ever stored.** `secure_url`/`url` from Cloudinary's
upload response are read at upload time (to confirm success) but not
persisted — access is always through a freshly-signed URL generated at
request time (`app/core/storage.py::get_signed_url`), computed in
`SellerController._to_document_response`. See
[../../../core/docs/storage.md](../../../core/docs/storage.md#delivery_type-public-vs-private-files)
for the underlying `delivery_type="authenticated"` mechanism.

## Relationships

```
accounts (1) ──── (0..1) sellers
sellers  (1) ──── (0..N) seller_documents
```
