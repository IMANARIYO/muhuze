import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from fastapi import UploadFile

from app.core.config import settings
from app.shared.exceptions.base import BadRequestError, ServiceUnavailableError


class StorageNotConfiguredError(ServiceUnavailableError):
    message = "File storage is not configured"


class UnsupportedFileTypeError(BadRequestError):
    message = "This file type is not allowed here"


class FileTooLargeError(BadRequestError):
    message = "This file is too large"


@dataclass(frozen=True, slots=True)
class UploadedFile:
    public_id: str
    url: str
    secure_url: str
    format: str | None
    resource_type: str
    delivery_type: str
    bytes: int


def _ensure_configured() -> None:
    if not (
        settings.cloudinary_cloud_name
        and settings.cloudinary_api_key
        and settings.cloudinary_api_secret
    ):
        raise StorageNotConfiguredError()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def _validate(
    file: UploadFile,
    *,
    allowed_content_types: set[str] | None,
    max_size_bytes: int | None,
) -> None:
    if (
        allowed_content_types is not None
        and file.content_type not in allowed_content_types
    ):
        raise UnsupportedFileTypeError(
            f"'{file.content_type}' is not allowed here — expected one of: "
            f"{sorted(allowed_content_types)}"
        )
    if (
        max_size_bytes is not None
        and file.size is not None
        and file.size > max_size_bytes
    ):
        raise FileTooLargeError(
            f"File is {file.size} bytes, which exceeds the {max_size_bytes}-byte limit "
            "for this upload"
        )


def _do_upload(
    file_obj: Any, *, folder: str, public_id: str, delivery_type: str
) -> dict[str, Any]:
    """Isolated so tests can monkeypatch this one function instead of the
    whole Cloudinary SDK. The SDK itself is synchronous — called via
    asyncio.to_thread so it doesn't block the event loop. upload_large
    (not upload) is used unconditionally: it handles both small and very
    large files via Cloudinary's chunked upload API, so callers never need
    to know or care how big a given file turns out to be."""
    return cloudinary.uploader.upload_large(
        file_obj,
        folder=folder,
        public_id=public_id,
        resource_type="auto",
        type=delivery_type,
    )


def _do_delete(public_id: str, *, resource_type: str, delivery_type: str) -> None:
    cloudinary.uploader.destroy(
        public_id, resource_type=resource_type, type=delivery_type
    )


def _do_get_signed_url(public_id: str, *, resource_type: str) -> str:
    url, _options = cloudinary.utils.cloudinary_url(
        public_id, resource_type=resource_type, type="authenticated", sign_url=True
    )
    return url


def _do_get_public_url(public_id: str, *, resource_type: str) -> str:
    url, _options = cloudinary.utils.cloudinary_url(
        public_id, resource_type=resource_type, type="upload", secure=True
    )
    return url


async def upload_file(
    file: UploadFile,
    *,
    folder: str,
    allowed_content_types: set[str] | None = None,
    max_size_bytes: int | None = None,
    delivery_type: str = "upload",
) -> UploadedFile:
    """Uploads `file` to Cloudinary under `folder` — e.g. "seller_verification",
    "products". Deliberately doesn't hardcode what folders/categories exist:
    each calling module owns its own folder name and validation rules
    (allowed content types, size limit), keeping this function reusable
    across every future upload feature rather than a registry to keep in
    sync. Raises StorageNotConfiguredError if Cloudinary credentials aren't
    set, UnsupportedFileTypeError / FileTooLargeError on failed validation
    — both checked before anything is sent over the network.

    `delivery_type`: "upload" (default) — publicly reachable via `url`/
    `secure_url`, fine for product images etc. "authenticated" — not
    publicly reachable at all; retrieve access via `get_signed_url()`,
    which produces a short-lived signed URL. Use "authenticated" for
    anything sensitive (identity documents, etc.) — never "upload".
    """
    _ensure_configured()
    _validate(
        file, allowed_content_types=allowed_content_types, max_size_bytes=max_size_bytes
    )

    public_id = uuid.uuid4().hex
    result = await asyncio.to_thread(
        _do_upload,
        file.file,
        folder=folder,
        public_id=public_id,
        delivery_type=delivery_type,
    )

    return UploadedFile(
        public_id=result["public_id"],
        url=result["url"],
        secure_url=result["secure_url"],
        format=result.get("format"),
        resource_type=result["resource_type"],
        delivery_type=result.get("type", delivery_type),
        bytes=result["bytes"],
    )


async def delete_file(
    public_id: str, *, resource_type: str = "image", delivery_type: str = "upload"
) -> None:
    _ensure_configured()
    await asyncio.to_thread(
        _do_delete, public_id, resource_type=resource_type, delivery_type=delivery_type
    )


async def get_signed_url(public_id: str, *, resource_type: str = "image") -> str:
    """A short-lived signed URL for a file uploaded with
    `delivery_type="authenticated"`. Cheap and offline — no network call,
    just HMAC-signs the URL locally — so this isn't wrapped in to_thread."""
    _ensure_configured()
    return _do_get_signed_url(public_id, resource_type=resource_type)


async def get_public_url(public_id: str, *, resource_type: str = "image") -> str:
    """A stable, unsigned URL for a file uploaded with
    `delivery_type="upload"` (the public/default case — product photos,
    brand logos, etc). Never use this for anything uploaded as
    "authenticated" — call `get_signed_url` for that instead. Cheap and
    offline, same as `get_signed_url`."""
    _ensure_configured()
    return _do_get_public_url(public_id, resource_type=resource_type)
