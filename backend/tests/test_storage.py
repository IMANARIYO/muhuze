import io

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core import storage
from app.core.config import settings
from app.core.storage import (
    FileTooLargeError,
    StorageNotConfiguredError,
    UnsupportedFileTypeError,
    delete_file,
    upload_file,
)


def make_upload_file(
    *,
    content: bytes = b"hello world",
    content_type: str = "image/png",
    filename: str = "test.png",
) -> UploadFile:
    return UploadFile(
        io.BytesIO(content),
        size=len(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


@pytest.fixture(autouse=True)
def _configured_cloudinary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test here goes through _ensure_configured — give it fake but
    truthy credentials so tests reach the actual logic under test instead
    of all failing on StorageNotConfiguredError."""
    monkeypatch.setattr(settings, "cloudinary_cloud_name", "test-cloud")
    monkeypatch.setattr(settings, "cloudinary_api_key", "test-key")
    monkeypatch.setattr(settings, "cloudinary_api_secret", "test-secret")


async def test_upload_raises_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    with pytest.raises(StorageNotConfiguredError):
        await upload_file(make_upload_file(), folder="test")


async def test_delete_raises_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "cloudinary_cloud_name", None)
    with pytest.raises(StorageNotConfiguredError):
        await delete_file("some-public-id")


async def test_upload_rejects_disallowed_content_type() -> None:
    file = make_upload_file(content_type="application/x-msdownload")
    with pytest.raises(UnsupportedFileTypeError):
        await upload_file(
            file, folder="test", allowed_content_types={"image/png", "image/jpeg"}
        )


async def test_upload_allows_permitted_content_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_do_upload(file_obj, *, folder, public_id):
        captured["folder"] = folder
        captured["public_id"] = public_id
        return {
            "public_id": public_id,
            "url": "http://res.cloudinary.com/x",
            "secure_url": "https://res.cloudinary.com/x",
            "format": "png",
            "resource_type": "image",
            "bytes": 11,
        }

    monkeypatch.setattr(storage, "_do_upload", fake_do_upload)

    result = await upload_file(
        make_upload_file(content_type="image/png"),
        folder="products",
        allowed_content_types={"image/png", "image/jpeg"},
    )

    assert captured["folder"] == "products"
    assert result.format == "png"
    assert result.bytes == 11
    assert result.public_id == captured["public_id"]


async def test_upload_rejects_file_over_size_limit() -> None:
    file = make_upload_file(content=b"x" * 1000)
    with pytest.raises(FileTooLargeError):
        await upload_file(file, folder="test", max_size_bytes=500)


async def test_upload_allows_file_within_size_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        storage,
        "_do_upload",
        lambda file_obj, *, folder, public_id: {
            "public_id": public_id,
            "url": "http://x",
            "secure_url": "https://x",
            "format": None,
            "resource_type": "raw",
            "bytes": 5,
        },
    )
    file = make_upload_file(content=b"small")
    result = await upload_file(file, folder="test", max_size_bytes=500)
    assert result.bytes == 5


async def test_delete_calls_sdk_with_given_public_id_and_resource_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_do_delete(public_id, *, resource_type):
        captured["public_id"] = public_id
        captured["resource_type"] = resource_type

    monkeypatch.setattr(storage, "_do_delete", fake_do_delete)

    await delete_file("abc123", resource_type="raw")

    assert captured == {"public_id": "abc123", "resource_type": "raw"}
