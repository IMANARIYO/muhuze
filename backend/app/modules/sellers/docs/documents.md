# Seller Documents

Cloudinary-backed identity document upload, via
[`app/core/storage.py`](../../../core/docs/storage.md) — nothing
Cloudinary-specific lives in this module; `SellerDocumentService` only
calls `storage.upload_file`/`delete_file`/`get_signed_url`.

## What's required to submit

`SellerService.submit_for_review` requires **at least one** uploaded
document — any document, regardless of the `document_type` value it was
labelled with. The presence of any row is enough.

Uploading no documents at all raises `MissingRequiredDocumentsError`
(422). The check (`_has_required_documents` in `service.py`) is
independent of upload contents: it only looks at whether any row exists.

## Validation

`SellerDocumentService.upload_document` passes these to `storage.upload_file`:

- `allowed_content_types = {"image/jpeg", "image/png", "application/pdf"}`
- `max_size_bytes = 10 * 1024 * 1024` (10 MB)
- `delivery_type = "authenticated"` — **never public**. See
  [storage.md](../../../core/docs/storage.md#delivery_type-public-vs-private-files).

Both checks happen before any network call, in `storage.py` itself.

## Privacy

Identity documents are sensitive. `secure_url`/`url` from the Cloudinary
upload response are **not persisted** — `SellerDocument` stores only
`cloudinary_public_id` and `cloudinary_resource_type`. Every read
(`GET /sellers/me/documents`, admin's `GET /sellers/{id}/documents`)
computes a fresh signed URL at request time
(`SellerController._to_document_response` → `storage.get_signed_url`).
A leaked database dump or log line containing a `public_id` alone doesn't
grant access to the file.

## Editability window

Upload/replace/delete are only allowed while the parent `Seller` is
`draft` or `rejected` — same rule as profile editing, see
[lifecycle.md#editability](lifecycle.md#editability). Attempting to
upload while `pending_review`/`active`/etc. raises `SellerNotEditableError`
(409), same exception `PATCH /sellers/me` uses for the same reason.

## Re-upload replaces, in place

At most one `SellerDocument` row per `(seller_id, document_type)` —
enforced by a unique constraint. Uploading a second file of a type that
already has one:

1. Uploads the new file to Cloudinary first.
2. Updates the *existing* row's `cloudinary_public_id` etc. (same row ID —
   not a new document, not a new list entry).
3. **Then** deletes the old Cloudinary asset, best-effort — if that
   delete fails, the failure is swallowed. By this point the database
   already points at the new file; failing the request over an orphaned
   old asset would be strictly worse than a single stray file sitting
   in Cloudinary.

Verified in `tests/test_seller_documents.py::test_reuploading_same_document_type_replaces_and_deletes_old_asset`.

### Deliberately not versioned

The original design discussion raised keeping every version
("`ID_FRONT` version 1 → rejected, version 2 → pending") for auditability.
**Not built.** Re-upload is a hard replace — the old version is gone once
the new one succeeds. This was an explicit scope cut, not an oversight:
version history adds real complexity (a `seller_document_versions` table
or a `version`/`is_current` column, admin UI to browse old versions) for a
benefit that only matters once there's an actual dispute-review need for
it. Revisit if that need shows up.

## Failure compensation

Two failure modes the design explicitly called out, both handled in
`SellerDocumentService.upload_document`:

**Cloudinary succeeds, then the database write fails.** The upload
happens *before* the `try` block that writes to the database. If
`documents.create`/`documents.replace` raises, the `except` clause deletes
the just-uploaded Cloudinary asset (best-effort — a failure there is
swallowed, since re-raising over a cleanup failure would hide the real
error) and re-raises the original exception. No orphaned file is left
pointing at nothing. Verified in
`tests/test_seller_documents.py::test_upload_cleans_up_cloudinary_asset_when_db_write_fails`
— it deliberately breaks the repository's `create` call and asserts the
Cloudinary delete still happened.

**Database succeeds, Cloudinary fails.** Simpler: `storage.upload_file`
itself raises before any database call happens, so there's nothing to
compensate — the request just fails cleanly with no partial state.

## What's not built

- **Document version history** — see [above](#deliberately-not-versioned).
- **Virus/malware scanning** — content-type and size are checked;
  actual file content isn't inspected beyond that.
- **Downloadable/streamed responses** — access is a signed URL the client
  fetches directly from Cloudinary, not proxied through this API.
