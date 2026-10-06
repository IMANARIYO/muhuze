# MUHUZE Global Link Backend — Engineering Rules

These rules are **mandatory** for every developer and every coding agent (Claude Code, Codex, Cursor, sub-agents, …) working in `backend/`. Read this file in full before modifying anything. If a rule blocks the task you were given, stop and ask. Don't work around it.

The goal is a clean, predictable, scalable, testable, production-ready backend. Don't introduce patterns, libraries, structures, or behaviors at random. **When an existing convention solves the problem, use it.**

## 1. Sources of truth

| Question | Authority |
|---|---|
| Business model, domain relationships, financial rules, invariants, open decisions | [`../README.md`](../README.md) |
| How backend code is structured, written, tested, and documented | **This file** |
| Response envelope, errors, pagination | [`docs/api/response-format.md`](docs/api/response-format.md) |
| Logging | [`docs/architecture/logging.md`](docs/architecture/logging.md) |
| A feature's requirements, status, progress | `docs/features/` (incl. `FEATURE-ROADMAP.md`) |
| Why an architectural choice was made | `docs/decisions/` (ADRs) |

If these disagree, **stop and report the conflict**. Never pick one silently. README §5 summarizes the code structure. If it ever drifts from this file, this file wins on code structure and the README wins on business rules.

## 2. Scope: no unrequested work

- Implement **only** what the user has explicitly approved. Planning or documenting a feature is not approval to build it.
- One feature at a time. Don't scaffold future features "while you're there".
- **Don't invent business rules**, rates, fees, limits, or real account details. If a missing decision blocks you, record it as `TO BE DECIDED` (README §20 / the feature doc) and ask.

## 3. Core principles

DRY · SOLID · separation of concerns · single responsibility · explicit dependencies · consistent errors, responses, validation, pagination, filtering, and authorization · testability · documentation · backward compatibility · minimal complexity.

Prefer the **simplest solution that meets the requirements**. Don't over-engineer, and don't under-engineer.

**DRY means no duplicated *knowledge*:** a business rule, such as product availability, lives in one place. It does not mean extracting a utility to save two repeated lines.

## 4. Before every change

1. Read this file.
2. Inspect the existing architecture, the relevant feature, and its services, repositories, schemas, tests, and docs.
3. Reuse existing infrastructure. Don't create new files or abstractions before understanding what exists.

Then answer: *Which feature am I changing? What code already handles this? Which service owns the rule? Can I reuse it? Does it need a schema change or migration? Authorization? Pagination, filtering, or sorting? What errors can occur? What does the response look like? Which tests and docs need updating?*

## 5. Development sequence

```
PLAN → DOCUMENT → DESIGN → IMPLEMENT → TEST → DOCUMENT AGAIN → VALIDATE → MARK PROGRESS
```

Code MUST NOT get ahead of its documentation, and documentation MUST NOT claim behavior that doesn't exist. When a feature changes: code → tests → API docs → feature docs → roadmap status, all together, never "at the end".

## 6. Architecture

**Modular monolith.** No microservices until an ADR shows a real reason to extract one.

```
backend/
├── app/
│   ├── main.py              # create_app(): logging, handlers, middleware, routers
│   ├── config/              # settings.py (pydantic-settings)
│   ├── core/                # logging, request_context_middleware, database, security, clock, model_registry
│   ├── api/                 # health_routes.py; v1/api_v1_routes.py aggregates feature routes under /api/v1
│   ├── domain/              # pure business rules & internal interfaces (no FastAPI/DB/provider code)
│   ├── infrastructure/      # adapters: payments/, storage/, notifications/, redis/, external_services/
│   ├── shared/              # responses/ (envelope, pagination), exceptions/ (AppError, handlers)
│   └── modules/<feature>/   # one folder per business feature
├── migrations/              # Alembic
├── scripts/
├── tests/{unit,integration,api,e2e}/
└── docs/{architecture,features,api,database,security,deployment,decisions}/
```

Create folders when the first real file needs them, never as empty scaffolding.

### File naming (mandatory, strict)

**For feature-specific Python modules, the feature name MUST appear in the file name:**

```
<feature>_<responsibility>.py
```

Before creating a file, ask: *which feature owns it?* and *what is its responsibility?* Then name it from those two answers. If a name doesn't clearly say FEATURE + RESPONSIBILITY, rethink it.

- **Responsibility suffixes**, used consistently: `_routes`, `_controller`, `_service`, `_repository`, `_schema`, `_model`, `_dependencies`, `_exceptions`, `_permissions`, `_mapper`, `_validator`, `_constants`.
- **The feature part is singular:** the `categories/` folder holds `category_service.py`, `products/` holds `product_model.py`, and `orders/` holds `order_routes.py`.
- **Forbidden for feature code:** `routes.py`, `route.py`, `controller.py`, `service.py`, `repository.py`, `schema.py`, `schemas.py`, `model.py`, `models.py`, `dependencies.py`, `exceptions.py`.
- Create a responsibility file **only when it's needed**. Never add an empty `order_controller.py` just to complete the pattern.

```
modules/categories/
├── category_routes.py      ✔        routes.py      ✘
├── category_service.py     ✔        service.py     ✘
├── category_repository.py  ✔        repository.py  ✘
├── category_schema.py      ✔        schemas.py     ✘
└── category_model.py       ✔        model.py       ✘
```

**Shared / core / API composition files** aren't owned by a feature, so they're named for their responsibility, still explicitly: `application_exceptions.py`, `exception_handlers.py`, `api_response.py`, `pagination.py`, `request_context_middleware.py`, `settings.py`. API version composition: `api/v1/api_v1_routes.py`, never `routes.py`.

**Tests:** `test_<feature>_<responsibility>.py`, in a folder per feature under each test level:

```
tests/unit/orders/test_order_service.py
tests/integration/orders/test_order_repository.py
tests/api/orders/test_order_routes.py
```

**Feature docs:** `docs/features/NNN_<feature>.md`, numbered in roadmap order: `001_authentication.md`, `002_users.md`, `003_roles_and_permissions.md`, `004_sellers.md`, `005_customers.md`, `006_categories.md`, `007_products.md`, `008_inventory.md`, `009_cart.md`, `010_orders.md`, `011_payments.md`, `012_wallets.md`, `013_referrals.md`, `014_notifications.md`, `015_admin.md`, `016_reporting.md`.

**Renames:** don't rename established files casually. If you're already modifying an area and find a file that violates this convention, fix it, as long as the rename doesn't needlessly disrupt imports or external references.

### Layer responsibilities

| Layer | Responsible for | Must NOT contain |
|---|---|---|
| **Routes** | Method, path, dependencies, request/response schemas, status code, calling the service | Business logic, DB queries, workflows, password, payment, or inventory logic, repeated validation, cross-feature rules |
| **Controller** (optional) | Real HTTP-level orchestration | Pass-throughs like `return service.x(...)`. If that's all it would do, omit it. |
| **Service** | Business rules, state transitions, ownership checks, transactions | HTTP concerns, raw SQL |
| **Repository** | Queries, inserts, updates, deletes, query composition | Business decisions |
| **Schema** | API contracts: request validation, response serialization | Business workflows |
| **Model** | Persistence entities and relationships | Use as the public API contract. Map Model → Service → Response schema. |

Consistency means **consistent responsibilities**, not identical file counts.

## 7. Cross-feature access

A feature uses another feature **only through its public service**. Never through its repository or tables.

```
OrderService → ProductService → ProductRepository      ✔
OrderService → ProductRepository                       ✘  (bypasses product rules)
```

This applies to users, products, inventory, orders, payments, wallets, referrals, notifications, and every other feature. Third-party providers are reached only through `infrastructure/` adapters behind internal interfaces. Business code never imports a provider SDK.

## 8. Errors: never swallow, always centralize

- **Never silently swallow exceptions.** `except Exception: pass`, or hiding a failure so an endpoint "succeeds", is forbidden. ruff enforces `BLE` and `S110`.
- Every `except` must have a purpose: catch → log (`logger.exception`) → translate into an application exception, or handle a specific expected case.
- Services raise **application exceptions** for expected failures: `BadRequestError`, `AuthenticationError`, `AuthorizationError`, `NotFoundError`, `ConflictError`, `InputValidationError`, `BusinessRuleError` (`app/shared/exceptions/application_exceptions.py`). Features subclass the closest one, and never invent new status mappings.
- Routes contain **no** large try/except blocks. The global handlers produce the error response.
- Unexpected exceptions reach the global boundary (`RequestContextMiddleware`), which logs them and returns a generic 500.
- Never expose stack traces, SQL errors, secrets, or internals to clients.

## 9. Response contract

Every endpoint returns the standard envelope. See [`docs/api/response-format.md`](docs/api/response-format.md).

```json
{ "success": true, "data": {}, "message": "Request successful", "status_code": 200 }
```

Declare `response_model=APIResponse[YourSchema]` and return `success_response(...)`. Never return ad-hoc dictionaries or invent a feature-specific format. Money is serialized as decimal strings.

## 10. Collection endpoints

Every list endpoint follows one pipeline, executed **in the database**, never by loading rows into memory:

```
Request → Validation → Filters → Search → Sorting → Pagination → Repository → Response
```

- **Pagination:** the shared `PaginationParams` (`page`, `page_size`; default 20, maximum 100) and `Page` (`items`, `page`, `page_size`, `total`, `total_pages`). No per-feature pagination parameters.
- **Filtering:** explicitly defined and validated parameters only (`status`, `category`, `seller`, `created_at`, `price`, …), backed by indexes where needed. Never accept arbitrary column names.
- **Sorting:** an explicit allowlist mapped to known fields. Never raw SQL fragments from clients.
- **Search** (`?q=`): document which fields are searched, case sensitivity, matching behavior, and the maximum query length. Use the same semantics everywhere unless there's a reason not to.

The shared filter, sort, and search helpers are added, and documented in `response-format.md`, when the first collection endpoint needs them.

## 11. Validation

- **Schema (API boundary):** shape and format. Example: quantity is a positive integer.
- **Service (business rules):** example: quantity does not exceed available stock.
- The backend is the final authority. Never rely on frontend validation.

## 12. Authentication, authorization, and security

- Authentication: *who are you?* Authorization: *are you allowed to do this?* Every protected operation enforces both.
- Check the **RBAC permission** (`require_permission`) **and resource ownership** (in the service). A permission never grants access to *another* user's resource. Admin access to resources the admin doesn't own is a separate, explicit permission.
- Permissions are code-defined (`*_permissions.py`) and synced to the database. Roles are dynamic data. Permission codes are `<resource>.<action>` with a **singular** resource: `product.create`, `role.manage`.
- Clients authenticate with a short-lived JWT access token (`Authorization: Bearer`) and an opaque, hashed, rotating refresh token. No cookies.
- The schema design lives in [`docs/database/database_schema.dbml`](docs/database/database_schema.dbml) (dbdiagram.io format). Add a table there, following its conventions, before writing its model.
- Never trust client-provided roles, permissions, prices, totals, amounts, seller IDs, or payment status. Hiding a button is not security.
- Security-sensitive logic (passwords, tokens, ownership, money) never lives in routes.

## 13. Transactions, concurrency, idempotency

- **Transactions are deliberate.** Operations that must succeed or fail together (for example: create order + order items + reserve stock) run in one transaction, owned by the **service**. Repositories never commit, and neither does the session dependency (`get_session` in `app/core/database.py`): whatever a service doesn't commit is rolled back when the request ends.
- **Concurrency:** assume simultaneous requests for inventory, wallets, payments, order status, referrals, and balances. Use constraints, row locks, atomic updates, and unique keys.
- **Idempotency:** retryable operations (payments, orders, wallet transactions, webhooks, notifications) must never create duplicate effects. Enforce it in the database, not only in code.

## 14. Financial and payment rules (non-negotiable)

These restate README §2 and §10–§14. The README wins on detail.

- **Money principle:** the buyer pays MUHUZE → MUHUZE accounts for each seller's earning → it settles from pending to available → the seller withdraws. Recording an earning is **not** paying the seller.
- **One confirmation path:** `Paid` only through the single `confirm_payment()`, whether verified manually (Phase 1, permissioned admin) or by a verified gateway confirmation (Phase 2). Downstream processing is identical for both.
- **Snapshots:** a SellerOrder keeps its commission terms, an OrderItem its product data, a Payment its destination, a Withdrawal its payout destination. Never recalculate history from current data.
- **Commission** comes only from the `seller_plans` resolver: an active plan first, then the configured default. Never hardcode a rate.
- **Ledgers:** balances change only through WalletTransactions. Financial records are append-only. Reversals are new, linked records, and nothing is deleted or edited to undo it.
- **Separation:** Payment ≠ Revenue ≠ SellerEarning ≠ Wallet ≠ Withdrawal. Subscription revenue ≠ commission. A MUHUZE payment destination is never a seller payout destination.
- **Payment data is sensitive:** keep payment logic behind the payment service and provider abstraction. Never scatter or hardcode payment instructions, numbers, codes, or accounts, and never expose more than the buyer needs.
- `Decimal`/`NUMERIC` for money, always with a currency. Never `float`.

## 15. Logging

See [`docs/architecture/logging.md`](docs/architecture/logging.md). Use `get_logger(__name__)`, put context in `extra=`, and keep messages constant (`"order created"`). Log errors, authentication failures, important business events, external-service failures, and performance problems.

**Never log** passwords, tokens, secrets, private keys, payment credentials, full account numbers, identity documents, or unnecessary personal data. Sensitive-looking `extra` keys are auto-redacted as a safety net, but message text is not, so never put sensitive values in messages.

## 16. Configuration

Never hardcode secrets, database URLs, API keys, provider credentials, or environment-specific values. Infrastructure configuration goes in `app/config/settings.py` via environment variables, and every new variable is documented in `.env.example`. Business parameters (rates, plans, payment destinations) are admin-managed data, not settings. `.env` is never committed.

## 17. Database

- Every schema change goes through an **Alembic migration** (`migrations/`, applied with `uv run alembic upgrade head`). Never alter a database by hand. Register a feature's first model file in `app/core/model_registry.py`. All timestamps are `timestamptz`, created with `utc_now()`.
- UUID primary keys unless an ADR says otherwise. `created_at`/`updated_at` on every table.
- Explicit foreign keys, unique and check constraints, and indexes based on real query patterns. Avoid N+1 queries.
- No queries from routes, and no duplicate query implementations. Use repositories.
- Soft delete only where justified and documented. Records referenced by financial history are deactivated, never deleted.

## 18. Dependencies

Before adding a package: does the project already solve this? Is the standard library enough? Can an existing dependency do it? Weigh maintenance and security. Add it only when justified, with **`uv add`** (`uv add --dev` for tooling), and mention it in your summary.

## 19. Architecture changes and compatibility

- No new architectural pattern without understanding the current one. For a significant change: explain the problem, propose a solution, consider alternatives, write an ADR, update the docs, and implement it consistently. Never silently restructure unrelated code.
- Once clients consume an API, don't casually rename fields, endpoints, statuses, or response structures. Breaking changes need a new API version.

## 20. Testing

- `tests/unit/` (isolated logic), `tests/integration/` (service + repository + real PostgreSQL), `tests/api/` (HTTP through the app, including authentication and authorization), `tests/e2e/` (critical workflows).
- Database tests use the `db_client` / `session_factory` fixtures (`tests/conftest.py`). They need `TEST_DATABASE_URL`, a database whose name ends with `_test`; its schema is rebuilt from the migrations on every run, and each test is rolled back.
- Tests are part of the feature. Critical business rules MUST be tested. Don't write meaningless tests to inflate coverage, and build depth as features stabilize.
- Financial tests assert **persisted records**, not just responses.
- **Never run the test suite yourself.** Give the user the command, and don't re-run it after each edit:

      cd backend && .venv/Scripts/python -m pytest -q

  Static checks are fine to run: `uv run ruff check .` and `uv run ruff format --check .`. Report honestly what is and isn't verified.

## 21. Documentation

Every major feature documents its purpose, requirements, business rules, dependencies, security, API behavior, database considerations, status, and progress. `docs/api/` must not contradict the generated OpenAPI. Write an ADR (`docs/decisions/ADR-NNN-<slug>.md`: context, decision, alternatives, consequences) for significant decisions only. Roadmap statuses: `PLANNED`, `DESIGNING`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `TESTING`, `COMPLETED`, `DEPRECATED`.

## 22. Definition of done

A feature is `COMPLETED` only when **all** of these hold. "The endpoint works" is not done.

```
[ ] Requirements          [ ] Routes                   [ ] Pagination/filtering where applicable
[ ] Architecture          [ ] Validation               [ ] Tests (user has run them and they pass)
[ ] Database + migration  [ ] Authentication           [ ] API documentation
[ ] Schemas               [ ] Authorization            [ ] Feature documentation
[ ] Repository            [ ] Error handling           [ ] Security review
[ ] Service               [ ] Standard responses       [ ] Performance review
[ ] Controller if needed  [ ] Logging reviewed         [ ] Roadmap status updated
```

## 23. Git

- Feature branches (`feature/<name>`), focused commits in conventional style (`feat(orders): …`, `test(auth): …`, `docs(payments): …`). Never mix unrelated features in one commit.
- **Commit only when the user explicitly asks. Push only when separately asked.**
- **Never mention Claude or any AI** in commits: no `Co-Authored-By` trailer, nothing in the message.
- Never rewrite pushed history unless asked.

## 24. When uncertain

```
DO NOT GUESS.              DO NOT BYPASS SERVICES.
DO NOT SWALLOW THE ERROR.  DO NOT BYPASS AUTHORIZATION.
DO NOT CREATE RANDOM CODE. DO NOT BYPASS VALIDATION.
DO NOT DUPLICATE LOGIC.    DO NOT IGNORE TESTS OR DOCUMENTATION.

INSPECT → UNDERSTAND → DESIGN → IMPLEMENT → TEST → DOCUMENT → VERIFY
```

Ask the user when blocked on a business decision. Report outcomes faithfully. Look before deleting or overwriting anything.
