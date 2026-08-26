from httpx import AsyncClient

from app.core.middleware import REQUEST_ID_HEADER


async def test_generates_request_id_when_absent(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert REQUEST_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) > 0


async def test_echoes_incoming_request_id(client: AsyncClient) -> None:
    response = await client.get("/health", headers={REQUEST_ID_HEADER: "test-correlation-id"})
    assert response.headers[REQUEST_ID_HEADER] == "test-correlation-id"
