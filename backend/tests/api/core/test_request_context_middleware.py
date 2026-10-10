import logging
import uuid

import pytest
from httpx import AsyncClient

from app.core.request_context_middleware import REQUEST_ID_HEADER


async def test_generates_request_id_when_absent(client: AsyncClient) -> None:
    response = await client.get("/health")
    uuid.UUID(response.headers[REQUEST_ID_HEADER])  # raises if not a UUID


async def test_echoes_valid_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={REQUEST_ID_HEADER: "client-abc_123"})
    assert response.headers[REQUEST_ID_HEADER] == "client-abc_123"


@pytest.mark.parametrize("bad_id", ["has spaces", "x" * 129, "semi;colon"])
async def test_replaces_unsafe_incoming_request_id(client: AsyncClient, bad_id: str) -> None:
    response = await client.get("/health", headers={REQUEST_ID_HEADER: bad_id})
    returned = response.headers[REQUEST_ID_HEADER]
    assert returned != bad_id
    uuid.UUID(returned)


async def test_access_log_records_request_without_query_string(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.access"):
        await client.get("/health", params={"token": "secret-value"})

    (record,) = [r for r in caplog.records if r.name == "app.access"]
    assert record.levelno == logging.INFO
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0
    assert "secret-value" not in caplog.text


async def test_access_log_level_follows_status(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="app.access"):
        await client.get("/does-not-exist")

    (record,) = [r for r in caplog.records if r.name == "app.access"]
    assert record.levelno == logging.WARNING
    assert record.status_code == 404
