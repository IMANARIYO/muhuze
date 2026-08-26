# MUHUZE Global Link

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async%20%28asyncpg%29-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-CC2927)
![Status](https://img.shields.io/badge/status-foundation%20in%20progress-yellow)

A digital marketplace and business platform connecting buyers, sellers, service providers, and communities through one integrated system — starting in Rwanda/East Africa with a design built to scale further.

MUHUZE is more than a product-listing site: it is intended to grow into an ecosystem spanning marketplace transactions, seller tools, buyer accounts, wallets, referrals, premium services, notifications, order management, and financial accounting.

---

## Table of Contents

- [Vision](#vision)
- [Why It Matters](#why-it-matters)
- [Tech Stack](#tech-stack)
- [Repository Layout](#repository-layout)
- [Project Status](#project-status)
- [Financial Architecture](#financial-architecture)
- [Core Business Rule — Seller Verification Gates Withdrawals](#core-business-rule--seller-verification-gates-withdrawals)
- [Engineering Principles for This Rebuild](#engineering-principles-for-this-rebuild)
- [Getting Started](#getting-started)
- [Pre-Launch Roadmap](#pre-launch-roadmap)

---

## Vision

MUHUZE Global Link aims to make digital commerce more accessible, organized, and scalable — connecting buyers and sellers, giving small businesses a real digital storefront, and turning marketplace activity into legitimate, trackable economic opportunity. The long-term goal is local-to-global infrastructure: start locally, prove the model, then scale internationally.

## Why It Matters

- **Connects buyers and sellers** — makes product discovery and selling easier.
- **Supports small businesses** — gives individuals and businesses a digital marketplace presence.
- **Encourages digital commerce** — helps more people participate in structured online buying and selling.
- **Creates economic opportunities** — supports legitimate income around marketplace activity.
- **Builds local-to-global infrastructure** — starts locally, designed to scale internationally.
- **Improves transaction organization** — links orders, payments, revenue, wallets, and withdrawals into one controlled financial flow.

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.14 |
| API framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x (async engine) |
| Database driver | asyncpg (PostgreSQL) |
| Migrations | Alembic (async template) |
| Auth | PyJWT + pwdlib (Argon2) |
| Settings | pydantic-settings |
| Package/dev tooling | uv, ruff, pytest, pytest-asyncio, httpx |

## Repository Layout

This backend follows a **modular/feature-based architecture** rather than one flat `controllers/services/models` tree — each business domain owns its own router, schemas, models, and service, so the codebase scales without every feature colliding in shared files.

```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       └── router.py     # aggregates every module's router under /api/v1
│   ├── core/                # config, database, security, logging, middleware — app-wide infrastructure
│   ├── db/
│   │   └── models.py         # central model registry — one import per model, read by alembic/env.py
│   ├── shared/               # cross-cutting building blocks reused by every module
│   │   ├── responses/        # standardized APIResponse[T] envelope + helpers
│   │   ├── exceptions/       # AppError hierarchy + global exception handlers
│   │   ├── dependencies/     # reusable FastAPI dependencies (pagination, etc.)
│   │   └── utils/
│   └── modules/               # one folder per business domain
│       ├── auth/  users/  sellers/  seller_verification/
│       ├── categories/  products/  orders/  payments/
│       ├── revenue/  referrals/  wallets/  withdrawals/
│       ├── notifications/  premium/  admin/
├── tests/
├── alembic/
└── pyproject.toml
```

Every module follows the same 4-layer convention:
- `router.py` — route declarations only (path, method, request/response schema); delegates to the controller.
- `controller.py` — the HTTP layer: translates request schemas to service calls and service results back to response schemas.
- `service.py` — business rules. No HTTP concerns, no direct SQL — calls the repository.
- `repository.py` — data access only (SQLAlchemy queries). No business rules.
- `schemas.py`, `models.py`, `dependencies.py`, `exceptions.py` round out each module.

Each module's router is included into `app/api/v1/router.py`, which `main.py` mounts once — so `main.py` never grows a long list of `include_router` calls as modules are built out.

**Module-owned docs.** Once a module has real content worth documenting, it gets its own `docs/` folder (`README.md` — purpose, responsibilities, explicit non-responsibilities; `database.md` — table-by-table schema; `roadmap.md` — done vs. planned, as a checklist). This repo's own README stays high-level and doesn't duplicate table schemas — see [`app/modules/auth/docs/`](backend/app/modules/auth/docs/) for the first one, built out alongside the `auth` module.

## Project Status

This repository is a **ground-up backend rebuild**. The infrastructure foundation is in place; business modules are scaffolded but not yet implemented.

**Done:**
- [x] Modular project structure (`core/`, `shared/`, 14 `modules/`)
- [x] Configuration via `pydantic-settings` + `.env`
- [x] Async SQLAlchemy engine, session factory, declarative `Base`
- [x] Alembic wired to app settings and models metadata
- [x] Standardized API response envelope (`status` / `message` / `data`)
- [x] Global exception handling (domain errors, validation errors, HTTP errors, unhandled exceptions) → one consistent response shape
- [x] Structured logging (JSON in production, readable text in development) with per-request correlation IDs
- [x] Test suite + CI-ready lint (`ruff`) for everything above
- [x] `/api/v1` router aggregation (`app/api/v1/router.py`, mounted once from `main.py`)
- [x] `Account` model (auth identity: email/phone/password_hash/is_active/is_verified) + migration
- [x] Auth: register (`POST /api/v1/auth/register`) and login (`POST /api/v1/auth/login`, JWT access + opaque refresh token)
- [x] `RefreshToken` model + migration — hashed, revocable, rotated on use (`POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`)
- [x] `get_current_account` dependency (`auth`) — JWT-gates any endpoint in any module
- [x] `Profile` model + migration (`users`, 1:1 with `Account`) — `GET/PUT /api/v1/users/me`
- [x] Email verification — OTP via `POST /api/v1/auth/email/verification/{request,confirm}` (sets `Account.is_verified`)
- [x] Password reset — `POST /api/v1/auth/password/{forgot,reset}` (single-use token, revokes all sessions on reset)
- [x] Authorization — `roles`/`permissions`/`account_roles`/`role_permissions`, seeded with `buyer`/`seller`/`admin`; every account gets `buyer` at registration; `require_role`/`require_permission` dependency factories for any module to use (`GET /api/v1/auth/me/authorization`)
- [x] Permission registry & sync — permissions are code-defined (each module's own `permissions.py`), reconciled into the database via `python -m app.scripts.sync_permissions`; roles stay dynamic (admin-manageable), permissions don't (see `auth/docs/permissions-sync.md`)
- [x] Startup account bootstrap — env-configured `admin` and `buyer`+`seller` test accounts, seeded idempotently every time the app starts (`app/core/bootstrap.py`, `main.py`'s `lifespan`); solves "how does the first admin get created" (see `auth/docs/bootstrap.md`)
- [x] Role/permission management — admin-only endpoints to grant/revoke an existing role on an account and an existing permission on a role; `require_permission` verified end-to-end (deny → assign → grant) even though no module has a real permission yet
- [x] Direct account permissions — a permission can also be granted straight to one account, bypassing roles; effective permissions = role-derived ∪ direct, deduplicated, GRANT-only (no DENY/override). Independent of role membership in both directions.
- [x] **Authentication and authorization considered fully implemented for what's been built so far**: register/login/refresh/logout, email verification, password reset, RBAC with dynamic role assignment, direct account permissions, and a code-synced permission catalog, plus a working bootstrap path for the first admin. 92/92 backend tests passing. See `auth/docs/roadmap.md` for the remaining gaps (phone verification/SMS; no module has a real permission to gate yet) and open questions.
- [x] File storage (`app/core/storage.py`) — reusable Cloudinary-backed upload/delete, module-agnostic (no hardcoded file categories; each future module owns its own folder + validation rules). Handles small and very large files transparently. No module consumes it yet — `seller_verification` (identity documents) is the obvious first. See `core/docs/storage.md`.
- [x] Real email delivery — `send_email` sends via SMTP (`aiosmtplib`) when configured, falls back to logging otherwise; no real SMTP credentials supplied yet. See `core/docs/notifications.md`.
- [x] Authentication module considered feature-complete for its scope — see `auth/docs/roadmap.md` for the two remaining gaps (real email delivery, phone OTP) and open questions

**Not yet built (scaffolded only):**
- [ ] Sellers (mid-build, paused — model/repository/service/controller/router written but not yet wired into the app), Seller Verification
- [ ] Categories, Products
- [ ] Orders (status lifecycle)
- [ ] Payments
- [ ] Revenue accounting
- [ ] Referrals
- [ ] Wallets
- [ ] Withdrawals
- [ ] Notifications, Premium, Admin

## Financial Architecture

The financial design keeps the frontend from ever directly creating or crediting money. Every money-related fact has exactly one place it's recorded:

| Record | Purpose |
|---|---|
| **Order** | The marketplace purchase and its lifecycle (`Pending → Accepted → Shipped → Delivered → Completed`, or `Rejected` / `Cancelled`). |
| **Payment status** | `Pending`, `Paid`, `Failed`, or `Refunded`. |
| **RevenueTransaction** | Accounting/revenue generated by a source — amount, currency, revenue rate, referral eligibility, status. |
| **Seller breakdown** | Seller amount, MUHUZE's cut, and seller earning, derived from the RevenueTransaction. |
| **ReferralCommission** | Eligible referral commissions (multi-level). |
| **WalletTransaction** | Wallet movements: commissions, withdrawals, refunds, adjustments. |
| **Wallet** | Current balances and totals (available, pending, earned, withdrawn). |
| **Withdrawal** | Controls movement of available funds out of the platform. |

**The most important pre-launch principle:** a successful build does not mean the platform is launch-ready. The real milestone is proving the *complete* financial lifecycle end to end — `payment → order → revenue → seller earning / referral eligibility → wallet accounting → withdrawal` — including cancellation, refund, and reversal. **The backend is the source of truth for financial operations; the frontend only displays and requests those operations.**

## Core Business Rule — Seller Verification Gates Withdrawals

> This section documents a business rule proven out in an earlier prototype of MUHUZE. It defines the target behavior for the `seller_verification` and `withdrawals` modules in this rebuild — it is **not** yet implemented in this codebase.

A user can become a seller and list products without being verified — but **a seller must be verified before they can withdraw money from their wallet.**

```
Register → Sell → Earn → Verify seller → Withdraw
```

A withdrawal request is only allowed once **both** are true:
1. The seller's verification record has `status = approved`.
2. The user's `sellerVerified` flag is `true`.

If either condition fails, the withdrawal is rejected with `SELLER_VERIFICATION_REQUIRED`. This exact rule was tested successfully in the prior prototype: an unverified user's withdrawal was correctly blocked, and after admin approval of their submitted identity documents, the same user could withdraw funds (fee deducted, net payout calculated correctly), which the admin could then move through `Pending → Processing → Completed`.

**Verification record covers:** identity documents (national ID / passport / driving license, front & back), personal information, address, phone, and an admin review trail (`reviewedBy`, `reviewedAt`, `rejectionReason`), with status `not_submitted → pending → approved | rejected`.

**Known gaps to close in the rebuild**, carried forward from the prototype:
- Real document upload/storage (previously just DB fields, no file storage wired up).
- Real phone OTP verification (previously stubbed to `false`).
- An admin verification dashboard (pending sellers, document review, approve/reject with reason).
- A clean wallet data model from day one — the prototype had to reconcile old top-level `balance`/`pendingBalance`/`currency` fields against a newer per-asset (`usd`/`rwf`) structure. This rebuild should settle on the final shape up front.

## Engineering Principles for This Rebuild

Carried forward as working rules for every financial feature built here:

- Change one financial flow at a time.
- Build backend source-of-truth logic first; the frontend requests and displays, never computes.
- Test with controlled accounts and known amounts.
- Verify the actual database records after every financial action — never trust a UI number until its backend accounting is verified.
- Keep git commits clear and recoverable.
- Only move toward public launch after end-to-end tests pass.

## Getting Started

```bash
cd backend
uv sync                      # install dependencies

cp .env.example .env         # fill in DATABASE_URL, JWT_SECRET_KEY, etc.

uv run fastapi dev app/main.py   # start the dev server → http://127.0.0.1:8000/docs

uv run pytest                # run the test suite
uv run ruff check .          # lint
```

## Pre-Launch Roadmap

The checklist below is the actual bar for "ready," not "the frontend builds":

- [ ] End-to-end marketplace testing with controlled buyer/seller/referrer accounts, exercising every order status.
- [ ] Payment → revenue integration: a `Paid` order creates the correct revenue record exactly once — never duplicated.
- [ ] Seller earnings → wallet: verify breakdown math and pending-to-available release.
- [ ] Referral commission testing: eligibility and Level 1/2/3 calculations under controlled transactions.
- [ ] Refund/reversal testing: cancellations and refunds correctly undo financial records without double-crediting.
- [ ] Withdrawal testing: balance checks, creation, status transitions, deductions, and failure handling.
- [ ] Security audit: JWT protection, ownership checks, unauthorized access, token handling on sensitive endpoints.
- [ ] Server-side validation of prices, quantities, IDs, currencies, and amounts.
- [ ] Financial reconciliation: cross-check Order, RevenueTransaction, ReferralCommission, WalletTransaction, and Wallet after every test.
- [ ] Production configuration: real database, URLs, CORS, and secrets — no localhost defaults.
- [ ] Logging that makes financial failures traceable without leaking sensitive data.
- [ ] Performance cleanup (bundle size, dynamic-import warnings on the frontend).
- [ ] UI/UX pass: desktop/mobile, loading/empty/error states, notifications, forms, navigation.
- [ ] Business/legal readiness: marketplace, seller, privacy, terms, refund, and withdrawal policies.
- [ ] Final acceptance test: registration → purchase → completion → financial release → referral → withdrawal, run as one controlled scenario.

**Recommended real test:** Buyer A, Seller B, Referrer C, a known-price product. Complete a successful payment, verify the order, complete the seller workflow, then inspect the RevenueTransaction, seller earning, eligible referral commissions, WalletTransaction, and Wallet balances before performing a controlled withdrawal. Repeat the same scenario with a cancellation/refund/reversal.

---

*Launch target: a controlled, tested, and financially consistent marketplace — not merely a successful build.*
