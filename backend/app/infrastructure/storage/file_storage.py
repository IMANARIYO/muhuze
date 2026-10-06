"""File storage behind one small interface.

Business code depends on `FileStorage` only and never imports a storage SDK.
Two kinds of file, never mixed:

- PRIVATE files (seller identity documents): there is no public link. A file
  is reached only through `private_url`, a signed link that stops working
  after a short time, which the owning feature hands out after its own
  access checks.
- PUBLIC images (product pictures): meant to be seen by anyone, served from
  a permanent URL built by `public_image_url`.

`build_file_storage` picks the adapter from settings: Cloudinary when its
credentials are configured, otherwise a stand-in that refuses every call.
"""

import asyncio
import io
import time
from dataclasses import dataclass
from typing import Protocol

import cloudinary.exceptions
import cloudinary.uploader
import cloudinary.utils

from app.config.settings import Settings

# Cloudinary's "authenticated" delivery type: the asset is not publicly
# reachable; every access needs a signature made with the API secret.
PRIVATE_DELIVERY_TYPE = "authenticated"
# Cloudinary's default delivery type: reachable by anyone who has the URL.
PUBLIC_DELIVERY_TYPE = "upload"
# Cloudinary stores JPEG, PNG, and PDF alike under the "image" resource type.
RESOURCE_TYPE = "image"


class FileStorageError(Exception):
    """The storage provider could not complete the request."""


class FileStorageNotConfiguredError(FileStorageError):
    """No storage credentials are configured (CLOUDINARY_* settings)."""


@dataclass(frozen=True, slots=True)
class StoredFile:
    """What must be kept to find a stored file again. Never a URL."""

    public_id: str
    resource_type: str
    format: str


@dataclass(frozen=True, slots=True)
class StoredImage:
    """A public image. `public_image_url` turns it back into a URL."""

    public_id: str
    format: str
    width: int | None
    height: int | None


class FileStorage(Protocol):
    async def upload_public_image(self, content: bytes, *, folder: str) -> StoredImage:
        """Store an image anyone may see, or raise FileStorageError."""

    async def delete_public_image(self, public_id: str) -> None:
        """Remove a public image, or raise FileStorageError."""

    def public_image_url(self, public_id: str, image_format: str) -> str:
        """The permanent URL of a public image. No network call."""

    async def upload_private(self, content: bytes, *, folder: str) -> StoredFile:
        """Store the bytes privately under `folder`, or raise FileStorageError."""

    async def delete(self, file: StoredFile) -> None:
        """Remove a stored file, or raise FileStorageError."""

    def private_url(self, file: StoredFile, *, expires_in: int) -> str:
        """A signed link to the file that stops working after `expires_in` seconds."""


class CloudinaryFileStorage:
    def __init__(self, settings: Settings) -> None:
        # Passed on every call instead of cloudinary.config(), which is
        # process-global state.
        self._credentials = {
            "cloud_name": settings.cloudinary_cloud_name,
            "api_key": settings.cloudinary_api_key,
            "api_secret": settings.cloudinary_api_secret.get_secret_value(),
        }

    async def upload_public_image(self, content: bytes, *, folder: str) -> StoredImage:
        try:
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                io.BytesIO(content),
                folder=folder,
                type=PUBLIC_DELIVERY_TYPE,
                resource_type=RESOURCE_TYPE,
                **self._credentials,
            )
        except (cloudinary.exceptions.Error, OSError) as exc:
            raise FileStorageError(f"upload failed: {type(exc).__name__}") from exc
        return StoredImage(
            public_id=result["public_id"],
            format=result["format"],
            width=result.get("width"),
            height=result.get("height"),
        )

    async def delete_public_image(self, public_id: str) -> None:
        try:
            await asyncio.to_thread(
                cloudinary.uploader.destroy,
                public_id,
                type=PUBLIC_DELIVERY_TYPE,
                resource_type=RESOURCE_TYPE,
                invalidate=True,
                **self._credentials,
            )
        except (cloudinary.exceptions.Error, OSError) as exc:
            raise FileStorageError(f"delete failed: {type(exc).__name__}") from exc

    def public_image_url(self, public_id: str, image_format: str) -> str:
        url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            format=image_format,
            type=PUBLIC_DELIVERY_TYPE,
            resource_type=RESOURCE_TYPE,
            secure=True,
            cloud_name=self._credentials["cloud_name"],
        )
        return url

    async def upload_private(self, content: bytes, *, folder: str) -> StoredFile:
        try:
            # The SDK is blocking, so it runs in a worker thread.
            result = await asyncio.to_thread(
                cloudinary.uploader.upload,
                io.BytesIO(content),
                folder=folder,
                type=PRIVATE_DELIVERY_TYPE,
                resource_type=RESOURCE_TYPE,
                **self._credentials,
            )
        except (cloudinary.exceptions.Error, OSError) as exc:
            raise FileStorageError(f"upload failed: {type(exc).__name__}") from exc
        return StoredFile(
            public_id=result["public_id"],
            resource_type=result["resource_type"],
            format=result["format"],
        )

    async def delete(self, file: StoredFile) -> None:
        try:
            await asyncio.to_thread(
                cloudinary.uploader.destroy,
                file.public_id,
                type=PRIVATE_DELIVERY_TYPE,
                resource_type=file.resource_type,
                invalidate=True,
                **self._credentials,
            )
        except (cloudinary.exceptions.Error, OSError) as exc:
            raise FileStorageError(f"delete failed: {type(exc).__name__}") from exc

    def private_url(self, file: StoredFile, *, expires_in: int) -> str:
        return cloudinary.utils.private_download_url(
            file.public_id,
            file.format,
            type=PRIVATE_DELIVERY_TYPE,
            resource_type=file.resource_type,
            expires_at=int(time.time()) + expires_in,
            **self._credentials,
        )


class UnconfiguredFileStorage:
    """Used when no storage credentials are set: every call fails clearly."""

    async def upload_public_image(self, content: bytes, *, folder: str) -> StoredImage:
        raise FileStorageNotConfiguredError()

    async def delete_public_image(self, public_id: str) -> None:
        raise FileStorageNotConfiguredError()

    def public_image_url(self, public_id: str, image_format: str) -> str:
        raise FileStorageNotConfiguredError()

    async def upload_private(self, content: bytes, *, folder: str) -> StoredFile:
        raise FileStorageNotConfiguredError()

    async def delete(self, file: StoredFile) -> None:
        raise FileStorageNotConfiguredError()

    def private_url(self, file: StoredFile, *, expires_in: int) -> str:
        raise FileStorageNotConfiguredError()


def build_file_storage(settings: Settings) -> FileStorage:
    if settings.is_file_storage_configured:
        return CloudinaryFileStorage(settings)
    return UnconfiguredFileStorage()
