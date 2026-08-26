# File Storage (`app/core/storage.py`)

## What it is

A thin, reusable wrapper around Cloudinary for any module that needs to
upload files — seller verification documents, product images, whatever
comes next. Deliberately doesn't know what kinds of files exist: each
calling module owns its own folder name and validation rules. There is no
central "file category" registry to keep in sync (same reasoning as
`auth/docs/permissions-sync.md`'s "don't invent permissions before a real
consumer exists" — don't invent folders/categories before a real module
needs one).

## API

```python
from app.core.storage import upload_file, delete_file, get_signed_url, UploadedFile

uploaded: UploadedFile = await upload_file(
    file,                                          # a FastAPI UploadFile
    folder="seller_verification",                  # your module's own folder name
    allowed_content_types={"image/jpeg", "image/png", "application/pdf"},
    max_size_bytes=10 * 1024 * 1024,                # optional
    delivery_type="authenticated",                  # "upload" (public, default) or "authenticated" (private)
)
# uploaded.public_id, .url, .secure_url, .format, .resource_type, .delivery_type, .bytes

await delete_file(
    uploaded.public_id,
    resource_type=uploaded.resource_type,
    delivery_type=uploaded.delivery_type,
)

# For delivery_type="authenticated" uploads: uploaded.url/.secure_url are NOT
# publicly reachable. Get access via a freshly-signed URL instead:
url = await get_signed_url(uploaded.public_id, resource_type=uploaded.resource_type)
```

`allowed_content_types` and `max_size_bytes` are both optional — omit
either to skip that check. Validation happens before anything is sent
over the network.

### `delivery_type`: public vs. private files

- `"upload"` (default) — publicly reachable at `url`/`secure_url` forever.
  Fine for product images, anything meant to be publicly visible.
- `"authenticated"` — **never** publicly reachable, regardless of guessing
  the URL. Use for anything sensitive — identity documents, etc. Retrieve
  access only via `get_signed_url()`, which HMAC-signs a URL locally (no
  network call). First real consumer: `sellers/docs/documents.md`.

**`delete_file` and `get_signed_url` both need the same `resource_type`
(and `delete_file` the same `delivery_type`) the file was uploaded
with** — Cloudinary can't locate/delete/sign an asset with the wrong
combination. Callers should persist `resource_type` (and know their own
`delivery_type`) alongside `public_id` — see how `SellerDocument` stores
`cloudinary_resource_type` for exactly this reason.

## Configuration

`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in
`.env`. All optional at the settings level — the app starts fine without
them. Calling `upload_file`/`delete_file`/`get_signed_url` without them
configured raises `StorageNotConfiguredError` (503) at call time, not at
startup.

## Large files

`upload_file` always calls Cloudinary's `upload_large` (chunked upload),
never plain `upload` — it handles both small and very large files
transparently, so callers never need to reason about file size when
choosing which SDK method to call.

## Errors

| Exception | Status | When |
|---|---|---|
| `StorageNotConfiguredError` | 503 | Cloudinary credentials aren't set |
| `UnsupportedFileTypeError` | 400 | `file.content_type` not in `allowed_content_types` |
| `FileTooLargeError` | 400 | `file.size` exceeds `max_size_bytes` |

## Testing

The actual Cloudinary SDK calls are isolated into
`_do_upload`/`_do_delete`/`_do_get_signed_url` — tests monkeypatch those
functions rather than the SDK, so nothing in the test suite makes a real
network call (signed-URL generation is HMAC-signing done locally, so
`get_signed_url` is actually exercised for real in tests — no network
call to fake). See `tests/test_storage.py`.

## Consumers

`sellers` (`SellerDocumentService`) is the first real consumer —
`delivery_type="authenticated"` for identity documents. See
[`sellers/docs/documents.md`](../../modules/sellers/docs/documents.md).
