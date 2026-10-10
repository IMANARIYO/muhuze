# Authentication API

**Status:** implemented (`app/modules/auth/`). Rules and rationale: [`docs/features/001_authentication.md`](../features/001_authentication.md).

All paths are under `/api/v1/auth`. Every response uses the [standard envelope](response-format.md); the tables below describe the `data` field.

## How a client uses it

```
register ──► (email: 6-digit code) ──► confirm ──► login ──► access token + refresh token
                                                               │
        call the API with  Authorization: Bearer <access token>│
                                                               ▼
                         on 401 ──► refresh ──► new access token + NEW refresh token
```

- Send the access token as `Authorization: Bearer <access_token>`. No cookies are used.
- The access token lasts `expires_in` seconds (900 by default). When it expires, call `/refresh`.
- **Every refresh returns a new refresh token and the old one stops working.** Store the new one. Never send two refresh requests at once with the same token: the second one is treated as a stolen token and logs the account out everywhere.

## Endpoints

| Method | Path | Auth | Success `data` | Purpose |
|---|---|---|---|---|
| POST | `/register` | – | `Account` (201) | Create an account and email a verification code |
| POST | `/email/verification/request` | – | `null` | Send a new code |
| POST | `/email/verification/confirm` | – | `null` | Confirm the code; the account can then log in |
| POST | `/login` | – | `Tokens` | Email + password → tokens |
| POST | `/refresh` | – (refresh token in body) | `Tokens` | Rotate the refresh token |
| POST | `/logout` | – (refresh token in body) | `null` | End that session. Always 200 |
| POST | `/logout-all` | Bearer | `null` | End every session of the account |
| GET | `/me` | Bearer | `Account` | The caller's account |
| GET | `/sessions` | Bearer | `Page<Session>` | The caller's active sessions, newest first. `page`, `page_size` |
| DELETE | `/sessions/{session_id}` | Bearer | `null` | End one of the caller's sessions |
| POST | `/password/change` | Bearer | `null` | Change password; ends every *other* session |
| POST | `/password/forgot` | – | `null` | Email a reset link. Always 200 |
| POST | `/password/reset` | – (reset token in body) | `null` | Set a new password; ends every session |

## Request bodies

| Endpoint | Body |
|---|---|
| `/register` | `email`, `password` (8–128 chars), `full_name` (1–150 chars), `phone` (optional, E.164: `+2507XXXXXXXX`) |
| `/email/verification/request` | `email` |
| `/email/verification/confirm` | `email`, `code` (6 digits) |
| `/login` | `email`, `password` |
| `/refresh`, `/logout` | `refresh_token` |
| `/password/change` | `current_password`, `new_password` (8–128 chars) |
| `/password/forgot` | `email` |
| `/password/reset` | `token`, `new_password` (8–128 chars) |

## Response objects

**Account**

```json
{
  "id": "0d6e…",
  "email": "amina@example.com",
  "phone": "+250788123456",
  "full_name": "Amina Uwase",
  "profile_picture": null,
  "status": "active",
  "is_verified": true,
  "created_at": "2026-10-05T17:30:00Z"
}
```

**Tokens**

```json
{ "access_token": "eyJ…", "refresh_token": "kR3…", "token_type": "bearer", "expires_in": 900 }
```

**Session**

```json
{
  "id": "5b1c…",
  "user_agent": "Mozilla/5.0 …",
  "ip_address": "197.243.0.10",
  "created_at": "2026-10-05T17:30:00Z",
  "expires_at": "2026-11-04T17:30:00Z",
  "is_current": true
}
```

`created_at` is when the session last logged in or refreshed. The session `id` changes on every refresh.

## Errors

| Status | Message | When |
|---|---|---|
| 400 | `Invalid or expired verification code` | Wrong, expired, used, or attempt-limited code; also unknown email or already-verified account |
| 400 | `Invalid or expired password reset token` | Unknown, expired, used, or superseded reset token |
| 400 | `Current password is incorrect` | `/password/change` |
| 401 | `Invalid email or password` | `/login`: wrong password or unknown email (indistinguishable) |
| 401 | `Invalid or expired refresh token` | `/refresh`: unknown, expired, revoked, or reused token |
| 401 | `Authentication required` | Missing, malformed, or expired access token; or the account is no longer active |
| 403 | `Email address is not verified` | `/login` with the correct password before verification. Send the user to the code screen |
| 403 | `This account is not active` | `/login` with the correct password on a suspended or deactivated account |
| 404 | `Session not found` | `DELETE /sessions/{id}`: not the caller's session, or already ended |
| 409 | `An account with this email already exists` | `/register` |
| 409 | `An account with this phone number already exists` | `/register` |
| 422 | field errors | Request validation (see [response-format.md](response-format.md)) |

`/email/verification/request` and `/password/forgot` return `200` with a fixed message whatever the email is, so they can't be used to find out which emails are registered.

Until machine-readable error codes are decided (README §20 `I3`), a client tells the two `403` login errors apart by `message`.
