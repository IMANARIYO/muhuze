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
from app.core.storage import upload_file, delete_file, UploadedFile

uploaded: UploadedFile = await upload_file(
    file,                                          # a FastAPI UploadFile
    folder="seller_verification",                  # your module's own folder name
    allowed_content_types={"image/jpeg", "image/png", "application/pdf"},
    max_size_bytes=10 * 1024 * 1024,                # optional
)
# uploaded.public_id, .url, .secure_url, .format, .resource_type, .bytes

await delete_file(uploaded.public_id, resource_type=uploaded.resource_type)
```

`allowed_content_types` and `max_size_bytes` are both optional — omit
either to skip that check. Validation happens before anything is sent
over the network.

## Configuration

`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in
`.env`. All optional at the settings level — the app starts fine without
them. Calling `upload_file`/`delete_file` without them configured raises
`StorageNotConfiguredError` (503) at call time, not at startup.

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

The actual Cloudinary SDK calls are isolated into `_do_upload`/`_do_delete`
— tests monkeypatch those two functions rather than the SDK, so nothing in
the test suite makes a real network call. See `tests/test_storage.py`.

## Not built yet

No module actually calls `upload_file` yet — `seller_verification` (which
needs identity document uploads, per the root README's core business rule
section) is the obvious first consumer, once that module itself exists.
