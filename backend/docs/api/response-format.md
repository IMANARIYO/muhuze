# API Response Format

**Status:** implemented (`app/shared/responses/`, `app/shared/exceptions/`, `app/core/request_context_middleware.py`).

Every endpoint uses one response contract. No feature may invent its own.

## Envelope

```json
{
  "success": true,
  "data": {},
  "message": "Request successful",
  "status_code": 200
}
```

| Field | Type | Meaning |
|---|---|---|
| `success` | bool | `true` for 2xx, `false` for every error. |
| `data` | object / array / null | The payload. Always `null` on errors. |
| `message` | string | Human-readable outcome. Safe to show to users on errors. |
| `status_code` | int | Always equal to the HTTP status code. |

Errors use the same shape:

```json
{ "success": false, "data": null, "message": "Product not found", "status_code": 404 }
```

## Writing an endpoint

```python
@router.get("/{product_id}", response_model=APIResponse[ProductOut])
async def get_product(product_id: UUID) -> JSONResponse:
    product = await product_service.get_product(product_id)
    return success_response(data=product, message="Product retrieved")


@router.post("", response_model=APIResponse[ProductOut], status_code=201)
async def create_product(payload: ProductCreate) -> JSONResponse:
    product = await product_service.create_product(payload)
    return success_response(data=product, message="Product created", status_code=201)
```

Rules:

- Always declare `response_model=APIResponse[...]`. It drives the OpenAPI docs.
- Always return `success_response(...)`. It sets the HTTP status **and** the body's `status_code` from one argument, so they can't disagree. Pass the same `status_code` you declare on the decorator.
- `data` must be a response schema (pydantic model), a list of them, or plain JSON values. Never pass database models (see AGENTS.md).
- Don't use `204 No Content`. Return `200` with `data: null`. `success_response` rejects non-2xx and 204 statuses.
- `Decimal` values are serialized as **strings** (`"100000.10"`), so money never passes through float.

## Errors

Services raise exceptions from `app/shared/exceptions/application_exceptions.py`. Routes don't catch them or build error JSON.

| Exception | HTTP | Use for |
|---|---|---|
| `BadRequestError` | 400 | Malformed or unusable request |
| `AuthenticationError` | 401 | Not authenticated / invalid credentials |
| `AuthorizationError` | 403 | Authenticated but not allowed |
| `NotFoundError` | 404 | Resource doesn't exist (or must not be revealed) |
| `ConflictError` | 409 | Duplicate / state conflict |
| `InputValidationError` | 422 | Input invalid in a way only the service can determine |
| `BusinessRuleError` | 422 | Valid request forbidden by a business rule |

Feature modules subclass the closest one, e.g. `class ProductNotFoundError(NotFoundError): message = "Product not found"`.

| Failure | Handled by | Response |
|---|---|---|
| `AppError` subclasses | `app_error_handler` | Its `status_code` + `message` |
| `HTTPException` (incl. unknown route 404, 405) | `http_exception_handler` | Its status; a non-string `detail` is replaced by the standard phrase. Headers (`Allow`, `WWW-Authenticate`) kept. |
| Request schema validation | `request_validation_handler` | 422; message lists **every** invalid field (`"email: Field required; age: …"`). Submitted values are never echoed. |
| Anything else (a bug) | `RequestContextMiddleware` | Logged with its stack trace and request id; client gets `500 "Internal server error"`, with no internal details. |

## Pagination

Collection endpoints return a `Page` inside `data`:

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "page": 1,
    "page_size": 20,
    "total": 57,
    "total_pages": 3
  },
  "message": "Request successful",
  "status_code": 200
}
```

Query parameters: `page` (default 1, ≥ 1) and `page_size` (default 20, 1–100). Use `PaginationParams` / `Page.build(...)` from `app/shared/responses/pagination.py`, and paginate in SQL, never in memory. The filtering, sorting, and search conventions are added to this document when the first collection endpoint needs them.

## Request ID

Every response has an `X-Request-ID` header. Clients may send their own (`[A-Za-z0-9._:-]`, up to 128 characters). An invalid ID is replaced with a generated UUID. Quote the request ID when reporting a problem: it matches every server log line for that request.

## Not yet decided

- **Machine-readable error codes.** The README requires `SELLER_VERIFICATION_REQUIRED` for blocked withdrawals, but the envelope has no `code` field. **To be decided** before the withdrawals feature: add an `error_code` field to the envelope, or rely on `message` and `status_code` only.
- **Per-field validation errors.** All field errors are currently joined into `message`. If forms need errors keyed by field, the envelope needs a structured `errors` field. **To be decided** with the frontend.
