# MUHUZE Global Link

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async%20%28asyncpg%29-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x-CC2927)
![Status](https://img.shields.io/badge/status-backend%20rebuild%20%E2%80%94%20domain%20design-yellow)

MUHUZE Global Link is a **multi-seller digital marketplace** connecting buyers, independent sellers, service providers, and communities through one integrated system. It is starting in Rwanda/East Africa, and the design is meant to scale beyond that.

This README is the **engineering specification and the single source of truth for business rules across the whole repository**, backend and frontend alike: what MUHUZE is, its business model, its domain relationships, its financial rules and invariants, and the order in which it is built. If code and this document disagree, one of them is wrong, so fix whichever one it is. Don't quietly let them drift apart.

> **Working on any part of MUHUZE?** Read the guide for the area you're changing (which defines *how* code is written there) and this README (which defines *what* the system must do):
>
> | Area | Guide |
> |---|---|
> | Backend | [`backend/AGENTS.md`](backend/AGENTS.md) |
> | Frontend | [`frontend/PROJECT.md`](frontend/PROJECT.md) |
> | Whole repo (tests, commits) | [`CLAUDE.md`](CLAUDE.md) |
>
> Those guides **must not restate or redefine business rules**. They link here instead. A business rule found anywhere else that isn't in this README is **not confirmed**: add it to [§20](#20-open-business-decisions) and ask.

---

## Table of Contents

1. [How to Read This Document](#1-how-to-read-this-document)
2. [What MUHUZE Is](#2-what-muhuze-is)
3. [Project Status](#3-project-status)
4. [Tech Stack](#4-tech-stack)
5. [Architecture](#5-architecture)
6. [Marketplace Domain Model](#6-marketplace-domain-model)
7. [Products, Categories, and Flexible Attributes](#7-products-categories-and-flexible-attributes)
8. [Cart and Checkout](#8-cart-and-checkout)
9. [Orders: Order → SellerOrder → OrderItem](#9-orders-order--sellerorder--orderitem)
10. [Seller Plans, Subscriptions, and Commission](#10-seller-plans-subscriptions-and-commission)
11. [Historical Correctness and Snapshots](#11-historical-correctness-and-snapshots)
12. [Payments and Gateway Integration](#12-payments-and-gateway-integration)
13. [Financial Architecture](#13-financial-architecture)
14. [Financial Invariants](#14-financial-invariants)
15. [Seller Verification Gates Withdrawals](#15-seller-verification-gates-withdrawals)
16. [Analytics](#16-analytics)
17. [Implementation Roadmap](#17-implementation-roadmap)
18. [Testing Requirements](#18-testing-requirements)
19. [Pre-Launch Checklist](#19-pre-launch-checklist)
20. [Open Business Decisions](#20-open-business-decisions)
21. [Engineering Principles](#21-engineering-principles)
22. [Getting Started](#22-getting-started)

---

## 1. How to Read This Document

The document uses three kinds of statement, and keeps them apart:

| Marker | Meaning |
|---|---|
| **MUST / MUST NOT** | A confirmed requirement or invariant. Implementation must comply, and it should be covered by a test. |
| *Recommended* | An engineering recommendation. Follow it unless there's a documented reason not to. |
| **Open** (IDs like `C1`, `P3`, `D5`; see [§20](#20-open-business-decisions)) | A business decision **that hasn't been made yet**. Don't settle it silently in code. Get the answer, then update this document. |

Entity names used here (`Order`, `SellerOrder`, `SellerPlan`, `SellerSubscription`, `WalletTransaction`, …) are **domain concepts**. They describe responsibilities and relationships, not final table or column definitions. The table-level design of each module lives in `backend/docs/database/` once the module is implemented ([§5.6](#56-documentation-ownership)).

Every amount, plan name, and rate in this document (10%, 50,000 RWF, `BUSINESS`, …) is an **example**, unless it is explicitly marked as confirmed. None of them may be hardcoded as a production rule.

## 2. What MUHUZE Is

The backend is designed around this combination. Every section of this document has to stay consistent with it:

```text
  A multi-seller marketplace                              (§6, §8, §9)
+ Flexible product/category system                        (§7)
+ Configurable seller subscription plans                  (§10)
+ Configurable commission system                          (§10)
+ Default commission for sellers without an active plan   (§10)
+ Manual/configured payments from day one                 (§12, Phase 1)
+ External payment-gateway-ready architecture             (§12, Phase 2)
+ Internal seller wallet/accounting system                (§13)
+ Seller withdrawals                                      (§13, §15)
+ MUHUZE platform financial analytics                     (§16)
+ Seller financial analytics                              (§16)
+ Auditable financial records                             (§13, §14)
```

### The core money principle

This is the foundation of the whole financial design. Every payment phase, provider, and module MUST preserve it:

```text
1. The buyer pays MUHUZE.                       (never the seller directly)
        ↓
2. MUHUZE accounts for each seller's earning.   (internal records per SellerOrder)
        ↓
3. The seller's wallet balance becomes available according to settlement rules.
        ↓
4. The seller withdraws.                        (the only way money leaves MUHUZE to a seller)
```

Recording an earning is **not** paying the seller. Money reaches a seller only through a completed withdrawal ([§13.1](#131-external-money-vs-internal-accounting)). How the buyer's payment reaches MUHUZE (manual transfer or gateway, [§12](#12-payments-and-gateway-integration)) never changes steps 2 to 4.

**Vision.** MUHUZE aims to make digital commerce more accessible, organized, and scalable:

- connect buyers and sellers;
- give small businesses a real digital storefront;
- encourage structured digital commerce;
- create legitimate, trackable economic opportunity;
- organize orders, payments, revenue, wallets, and withdrawals into one controlled financial flow.

It starts locally, proves the model, then scales internationally.

## 3. Project Status

This repository is a **ground-up backend rebuild**.

**Current state:** the previous `backend/` was removed (commit `ff5742a`, "start project again"), and the backend is being rebuilt from scratch. The repository currently holds:

| Path | What it is |
|---|---|
| `README.md` | This specification. |
| `backend/` | The rebuild. Engineering rules are in [`backend/AGENTS.md`](backend/AGENTS.md). **Implemented so far:** settings, the standard response envelope, centralized exception handling, structured logging with request IDs, `/health`, the `/api/v1` router, the database layer with Alembic migrations, **authentication**, **roles and permissions**, **sellers** with private document storage, seller-owned **categories**, and **products** (the last two awaiting their first passing test run; see [`backend/docs/features/`](backend/docs/features/FEATURE-ROADMAP.md)). Seller plans are next. |
| `frontend/` | Frontend (Vite + React + TypeScript), currently on demo data. It displays data and requests operations. It never computes or mutates money. Its guide is [`frontend/PROJECT.md`](frontend/PROJECT.md), which defers to this README for business rules. |
| `old project/` | The original prototype, kept for reference. |

**Previous backend implementation (reference only).** The last full backend is preserved in git history at commit `4d7011c` (`git show 4d7011c:backend/...`). It implemented auth, users, RBAC, sellers, and parts of the catalog, commerce, and wallets. The **architecture decisions** below were proven there and carry forward into the rebuild. The **code** has to be rebuilt on `main` before any of it counts as done.

Decisions carried forward from the previous implementation:

- A modular, feature-based layout with layered modules: routes → (optional controller) → service → repository ([§5](#5-architecture)).
- A standard response envelope, a global exception hierarchy (`AppError`) with handlers, structured logging with per-request correlation IDs, and `/api/v1` router aggregation mounted once from `main.py`. These are now rebuilt, and the envelope changed to `{success, data, message, status_code}` (see [`backend/docs/api/response-format.md`](backend/docs/api/response-format.md)).
- **Auth:** `Account` (email/phone/password hash/status/is_verified), JWT access tokens plus opaque, hashed, revocable refresh tokens that rotate on use, email verification by OTP, and password reset with a single-use token that revokes every session. The rebuilt rules are in [§5.4](#54-authorization-and-ownership).
- **One `accounts` table for every person**, whatever their roles. Basic personal info (name, photo) lives on the account; role-specific data, such as the seller business profile, lives in its own 1:1 table. (The previous implementation kept a separate `Profile` table; that is merged into the account.)
- **RBAC:** dynamic, admin-manageable roles (seeded `buyer` / `seller` / `admin`, and every account gets `buyer`). Permissions are **code-defined** in each module's `permissions.py` and synced into the database. Effective permissions are role-derived ∪ direct account grants (grant-only, no deny). `require_role` / `require_permission` dependencies are available to every module.
- **Startup bootstrap** of env-configured admin and test accounts, run idempotently. This answers "how does the first admin get created?"
- **File storage** is Cloudinary-backed and module-agnostic (now `backend/app/infrastructure/storage/file_storage.py`), with private/authenticated delivery for sensitive files such as identity documents.
- **Sellers:** `Seller` is 1:0..1 with `Account` and separate from the `seller` RBAC role. Seller status is the operational gate, while the role only marks a seller who has been approved at least once. Seller status never affects the account's ability to log in or to buy.

**Superseded earlier schema draft.** A `database-schema.dbml` draft (removed from the working tree, still available in git history) predates the requirements in this README. Where they conflict, this README wins:

| Draft design | Superseded by |
|---|---|
| `revenue_transactions` has one row per **order**, with a single `seller_id` and `unique(order_id)` | One revenue record per **SellerOrder** ([§13.3](#133-records-and-their-responsibilities)). |
| `seller_orders` created at payment time | `SellerOrder` created at **checkout** with its commercial-terms snapshot, and **released to the seller** once payment is `Paid` ([§8](#8-cart-and-checkout), [§9.3](#93-status-at-two-levels)). |
| Hardcoded commission rates (12% basic / 7% premium) and fixed premium plans | Admin-configurable `SellerPlan`s and a configurable default rate ([§10](#10-seller-plans-subscriptions-and-commission)). |
| Products as an admin-curated shared catalog, with sellers selling through `seller_listings` | Products are **owned by a seller** ([§7.1](#71-product-ownership)). Whether a shared catalog is ever needed is **Open** (`K5`). |
| A single payment provider (Airtel Money) wired directly into the payment flow | A provider abstraction behind an internal `Payment` record ([§12](#12-payments-and-gateway-integration)). |

## 4. Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.14 |
| API framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x (async engine) |
| Database / driver | PostgreSQL / asyncpg |
| Migrations | Alembic (async template) |
| Auth | PyJWT + pwdlib (Argon2) |
| Email | aiosmtplib (SMTP), behind an internal `EmailSender` interface |
| File storage | Cloudinary (private assets, signed expiring links), behind an internal `FileStorage` interface |
| Settings | pydantic-settings |
| Tooling | uv, ruff, pytest, pytest-asyncio, httpx |

## 5. Architecture

### 5.1 Layout

The backend is a **modular monolith with feature-based modules**. Each business domain owns its own routes, schemas, models, services, and repositories, so features don't collide in shared files as the codebase grows. The binding code-structure rules, including the **mandatory file naming convention**, are in [`backend/AGENTS.md`](backend/AGENTS.md).

```
backend/
├── app/
│   ├── main.py                 # create_app(): logging, exception handlers, middleware, routers
│   ├── config/                 # settings.py
│   ├── api/v1/api_v1_routes.py # aggregates every module's routes under /api/v1 (mounted once)
│   ├── core/                   # logging, request-context middleware, database, security
│   ├── domain/                 # pure business rules and internal interfaces
│   ├── infrastructure/         # adapters for external systems (payments, storage, notifications, redis)
│   ├── shared/                 # cross-cutting building blocks
│   │   ├── responses/          # api_response.py (envelope), pagination.py
│   │   └── exceptions/         # application_exceptions.py, exception_handlers.py
│   └── modules/                # one folder per business domain
│       ├── auth/  users/
│       ├── sellers/  seller_verification/
│       ├── categories/         # each seller's own categories + their attribute definitions
│       ├── products/           # seller-owned products + ProductAttributeValues
│       ├── seller_plans/       # SellerPlans, SellerSubscriptions, default commission, commission resolver
│       ├── carts/
│       ├── orders/             # Order, SellerOrder, OrderItem
│       ├── payments/           # internal Payment record, MUHUZE payment destinations, confirmation workflow
│       │   └── providers/      # confirmation channels behind a common interface: manual (Phase 1), gateways (Phase 2)
│       ├── revenue/            # transaction commission revenue, subscription revenue, …
│       ├── wallets/
│       ├── withdrawals/        # withdrawals + seller payout destinations
│       ├── analytics/          # read-only seller and platform analytics
│       ├── referrals/  notifications/  premium/  admin/
├── migrations/                 # Alembic
├── tests/{unit,integration,api,e2e}/
├── docs/                       # architecture, features, api, database, security, deployment, decisions
└── pyproject.toml
```

Module names may be adjusted during implementation. The **responsibility boundaries** may not.

### 5.2 Layers and file naming

```
routes  →  (controller, only when useful)  →  service  →  repository
```

Feature files are always named `<feature>_<responsibility>.py`. Generic names such as `service.py` or `models.py` are forbidden for feature code.

| File (orders example) | Responsibility | Must not contain |
|---|---|---|
| `order_routes.py` | Method, path, dependencies, request/response schemas, status code. | Business logic, DB queries. |
| `order_controller.py` | *Optional:* real HTTP-level orchestration only. | Pass-through calls; business rules. |
| `order_service.py` | **Business rules**, state transitions, ownership checks, financial calculations, transaction boundaries. | HTTP concerns, raw SQL. |
| `order_repository.py` | Data access only (SQLAlchemy queries). | Business rules. |
| `order_schema.py`, `order_model.py`, `order_dependencies.py`, `order_exceptions.py`, `order_permissions.py`, … | Supporting pieces, created only when needed. | — |

### 5.3 Architectural rules

- **Routes contain no business logic.** Controllers, where they exist, only orchestrate HTTP. **Services own business rules.** Repositories only access data.
- **Financial logic lives only in backend services.** No financial value (price, total, commission, earning, balance, payment status) is ever taken from the client as truth. The client sends *intent* (product IDs, quantities, "start payment"), and the backend determines everything else.
- **Ownership and authorization are enforced server-side**, in the service layer, on every request ([§5.4](#54-authorization-and-ownership)).
- **Modules stay loosely coupled.** A module uses another module only through that module's **service-level functions**. It never imports another module's repository or writes another module's tables directly. One example: `orders` asks `seller_plans` for the applicable commercial terms; it does not read subscription rows itself.
- **Provider-specific details stay inside `payments/providers/`.** Orders, revenue, and wallets never see a gateway's payload, status names, or SDK ([§12.4](#124-payment-provider-abstraction)).
- **Each business rule lives in one place.** Commission resolution, payment confirmation, order-status derivation, settlement release, and the withdrawal gate each live in exactly one service function, and every caller uses that function.
- **Avoid premature abstraction.** Build the concrete flow first. Extract shared abstractions only once a second real use exists. The payment provider interface is the deliberate exception, because provider independence is a stated requirement.
- **Money is never a float.** Use `Decimal` in Python and `NUMERIC` in PostgreSQL, and always store the amount together with its currency.

### 5.4 Authorization and ownership

The existing RBAC system is the foundation for every marketplace authorization check. Two separate questions are answered for every protected operation:

1. **Permission (RBAC):** may this account perform this *kind* of action? For example, `product.update`. This is checked with `require_permission`.
2. **Ownership (service layer):** does this *specific* resource belong to the acting seller or buyer? For example, `product.seller_id == current_seller.id`.

Both must pass. Holding `product.update` never grants the right to update *another seller's* product. Admin access to resources the admin doesn't own is a **separate, explicit permission**, never an implicit bypass of the ownership check. Sensitive financial actions, such as managing MUHUZE payment destinations, manual payment approval, plan and default-rate changes, withdrawal approval, and adjustments, each get their own explicit permission. Seller *status* (active, suspended, …) is a third, operational gate, checked by the service.

**Conventions (decided):** permissions are named `<resource>.<action>` with a **singular** resource (`product.create`, `role.manage`). Clients authenticate with a short-lived JWT **access token** in the `Authorization: Bearer` header, plus an opaque, rotating **refresh token**; cookies are not used.

**Roles and permissions rules (decided):**

- A **permission** is one allowed action. Permissions are defined by the system, one set per resource, and cannot be created or edited by anyone at runtime.
- A **role** is a named bundle of permissions. Admins can create, rename, and delete roles and choose their permissions.
- Three **system roles** always exist and cannot be renamed or deleted: `buyer` (every account, from registration), `seller` (given when a seller application is approved), and `admin`.
- The **`admin` role always holds every permission**, including ones added later. Its permissions cannot be edited.
- A permission can also be granted **directly to one account**. An account's permissions are those of all its roles plus its direct grants. There is no "deny".
- An admin cannot remove the `admin` role from their own account.
- The **first admin** is created at startup from environment settings, because otherwise nobody could grant the role.

Details: [`backend/docs/features/003_roles_and_permissions.md`](backend/docs/features/003_roles_and_permissions.md).

**Authentication rules (decided):**

- **An account must verify its email before it can log in.** Registration emails a one-time code; login is refused until the code is confirmed.
- Only an `active` account can log in or use a token. A `suspended` (by an admin) or `deactivated` (by its owner) account is locked out at once.
- One-time codes expire, work once, and stop working after a limited number of wrong guesses.
- Each login is a separate **session** that its owner can list and end. A refresh token works once; presenting one that was already exchanged ends every session of the account, because it means the token leaked.
- Changing the password ends every other session. Resetting a forgotten password ends all of them.
- Responses never reveal whether an email is registered, except the "already exists" answer at registration.

Lifetimes and limits are configuration (`backend/.env.example`). The full rules, and what is still missing (notably rate limiting), are in [`backend/docs/features/001_authentication.md`](backend/docs/features/001_authentication.md).

### 5.5 Configuration

Infrastructure settings (database URL, secrets, payment-provider credentials) come from environment variables through `app/config/settings.py`. **Business parameters** that affect money, such as the default commission rate, plans, fees, and limits, belong to the module that owns that business rule. They are admin-manageable, readable from one place, and never hardcoded across the codebase ([§10.4](#104-default-commission-rate)).

**Real payment details never live in the repository.** MUHUZE's receiving phone numbers, merchant/MoMo codes, bank accounts, and registered names are **admin-managed data** ([§12.3](#123-muhuze-payment-destinations)). Provider API keys and webhook secrets are **environment secrets**. Neither may appear in source code, seed files, tests, or git history. Examples in this document use placeholders such as `[configured number]`.

### 5.6 Documentation ownership

This root README stays **high-level**: business model, domain relationships, architecture, financial principles and invariants, roadmap, and open decisions. It deliberately doesn't list every column.

Detailed documentation lives in `backend/docs/`:

```
backend/docs/
├── features/      # NNN_<feature>.md per feature (e.g. 010_orders.md) + FEATURE-ROADMAP.md
├── api/           # endpoint behavior and contracts (response-format.md, …)
├── database/      # table-level design
├── architecture/  # overview, logging, …
├── security/  deployment/
└── decisions/     # ADRs
```

The previous implementation's module docs (auth, users, sellers, categories, products) can be read from history, e.g. `git show 4d7011c:backend/app/modules/sellers/docs/lifecycle.md`. Treat them as reference material. Where they conflict with this README, this README wins.

## 6. Marketplace Domain Model

### 6.1 MUHUZE is multi-seller

MUHUZE is **not** a single-seller shop. Many independent sellers list products on the platform, and **one buyer checkout can contain products from many sellers**:

```
Buyer
  │
  └── Order #10001
        ├── Seller A
        │     ├── Product A1
        │     └── Product A2
        ├── Seller B
        │     └── Product B1
        └── Seller C
              ├── Product C1
              └── Product C2
```

The system **MUST NOT** be modelled as `Order → one seller`. It also **MUST NOT** split one checkout into several independent orders just because the products come from different sellers.

### 6.2 Actors

| Actor | Represented by | Notes |
|---|---|---|
| Buyer | `Account` | Every account can buy. |
| Seller | `Seller` (1:0..1 with `Account`) | A seller is also an account, and seller status never affects that account's ability to buy. |
| Admin | `Account` with admin role/permissions | Platform operations, reviews, configuration. |
| Payment provider | External system (MoMo/bank account in Phase 1, gateway in Phase 2) | Receives the buyer's money into a MUHUZE-controlled destination. In Phase 2 it talks to MUHUZE through an adapter. It is never trusted without verification ([§12](#12-payments-and-gateway-integration)). |

### 6.3 Domain map

```
Account ──1:0..1── Seller ──1:N── Product ──N:1── Category ──1:N── AttributeDefinition
   │                 │               │                                   │
   │                 │               └──1:N── ProductAttributeValue ─────┘
   │                 │
   │                 ├──1:N── SellerSubscription ──N:1── SellerPlan   (commercial terms over time)
   │                 ├──1:1── Wallet ──1:N── WalletTransaction
   │                 ├──1:N── SellerPayoutDestination        (where the seller receives withdrawals)
   │                 └──1:N── Withdrawal ──N:1── SellerPayoutDestination
   │
   ├──1:1── Cart ──1:N── CartItem ──N:1── Product
   │
   └──1:N── Order ──1:N── SellerOrder ──1:N── OrderItem ──N:1── Product (reference only;
                │              │                                 snapshot is authoritative)
                │              └──1:1── RevenueTransaction / SellerEarning
                └──1:N── Payment ──1:N── ProviderTransaction   (attempts; at most one successful, see §12)
                            └──N:1── PaymentDestination         (MUHUZE-controlled receiving account; snapshotted)

PaymentMethod ──1:N── PaymentDestination        (admin-managed; never a seller's account)
```

`PaymentDestination` (where **buyers pay MUHUZE**) and `SellerPayoutDestination` (where **MUHUZE pays a seller**) are completely separate concepts. Neither may stand in for the other.

The cardinalities show the intended relationships. Where a cardinality depends on an open decision (for example, split payments, `P2`), the decision is tracked in [§20](#20-open-business-decisions).

## 7. Products, Categories, and Flexible Attributes

### 7.1 Product ownership

- **Every product belongs to exactly one seller:** `Seller 1 ── N Product`.
- **Every product belongs to one category of its own seller:** `Category 1 ── N Product`, and the category's seller is the product's seller.
- Within the category structure and marketplace rules, a seller is free to decide **what** they sell. A seller **can sell across multiple categories**, and the system MUST NOT assume a seller belongs to one category. Whether some categories are restricted, such as regulated goods, is **Open** (`K6`).
- A seller can create, update, and archive **only products they own**. This is enforced through RBAC permission plus the ownership check ([§5.4](#54-authorization-and-ownership)).
- All sellers share **one product model** (the same core fields). Categories and their attributes are each seller's own ([§7.2](#72-seller-owned-categories)).

### 7.2 Seller-owned categories

**Decided 2026-10-06 (`K7`): each seller creates and owns the categories of their own shop.** There is no shared, marketplace-wide category tree. (This replaces the earlier design of one shared tree managed by the marketplace.)

```
Seller A's shop                  Seller B's shop
  ├── Phones                       ├── Smartphones
  ├── Phone accessories            └── Laptops
  └── Tablets
```

- A category **belongs to exactly one seller** and is used only by that seller's products. Seller A's "Phones" and seller B's "Smartphones" are unrelated records.
- Categories are **flat**: no parent and no subcategories.
- **The seller defines the attributes** of each of their categories ([§7.3](#73-products-dont-all-have-the-same-structure)).
- Only the owning seller, while `active`, creates, renames, reorders, or removes their own categories and attributes. Staff can hide one that breaks the rules.
- A category name is unique within a shop, ignoring letter case; two shops can use the same name.
- An attribute's **type cannot be changed** once created, and each attribute has a stable key that survives renaming, so product data stays valid.
- A category hidden by staff cannot be switched back on by its seller.
- Buyers see only active categories, attributes, and options, and only for a shop that is open.

Details: [`backend/docs/features/006_categories.md`](backend/docs/features/006_categories.md).
- Only **products for sale** are covered. Rental and service listings are not (`X1`).

**What this means for buyers.** Buyers browse by category *inside a shop*, and find products across shops by **search**. They cannot browse "all Phones" across the marketplace, because nothing ties one seller's category to another's. If cross-shop browsing is wanted later, it is added as a separate short list of marketplace departments that a product also points to (`K9`); it does not replace seller-owned categories.

### 7.3 Products don't all have the same structure

Different categories need different attributes:

```
Phones     → brand, model, RAM, storage, color
Shoes      → brand, size, material, color
Furniture  → material, dimensions, weight, assembly requirements
```

So the product model is a **common core plus flexible, category-defined attributes**.

**Common product core.** It holds only fields that are genuinely common to every marketplace product:

```
Product
- id
- seller_id
- category_id
- name
- description
- base price
- currency
- status
- timestamps
```

**Flexible attributes:**

```
Category
  └── AttributeDefinition      (what attributes a product in this category has:
                                name, data type, unit, required?, allowed values, filterable?, …)
Product
  └── ProductAttributeValue    (this product's value for one AttributeDefinition)
```

**Why this approach:**

- A single products table holding every possible field ("RAM", "shoe size", "assembly required", …) would be mostly empty columns. Every new category would also need a schema migration, and nothing could validate which fields apply to which category.
- With attribute definitions owned by categories, **adding a new category or attribute is a data operation, not a schema change**. The core product schema stays stable as MUHUZE adds new kinds of goods.
- Definitions give the backend a contract to **validate against**: required attributes, data types, and allowed values. Product attributes are therefore checked server-side rather than being free-form text.
- Filterable definitions support category-specific search and filtering ("phones with 8GB RAM").

**Rules:**

- Attribute values are validated **in the products service** against the category's definitions.
- The product core MUST NOT gain category-specific columns.
- Attribute values are stored as **typed rows**, each pointing at a real attribute and, for choices, a real option (`K2`, decided).
- There are **no variants** (`K1`, decided), and nothing to inherit, because categories are flat.

### 7.4 Product rules

**Decided 2026-10-07:**

- **One product, one price.** No variants: a phone in two storage sizes is two products (`K1`).
- **Lifecycle:** `draft → published ⇄ archived`. A draft may be incomplete.
- **To be published**, a product needs an active category, a value for every required attribute of that category, and at least one picture. A published product must stay complete: an edit that would break this is refused.
- **No approval step.** A product is on sale as soon as its seller publishes it. Staff can hide one that breaks the rules, and its seller then cannot publish it (`K4`).
- **Published products are never deleted, only archived**, so that later orders can still refer to them. Only a draft that was never published can be deleted.
- **What products use cannot be deleted:** a category that still has products, and an attribute or option that products have values for, can only be switched off (`K8`).
- **Price** is in **RWF** only for now (`T2`), more than zero, with at most two decimal places.
- **Pictures:** up to 8 per product, JPEG or PNG, 5 MB each, public.
- **Stock is not tracked yet** (`K3`): a published product is simply available. Inventory is a separate feature and must exist before orders.
- **Buyers see a product only when** it is published, not hidden by staff, its category is active, and its shop is open. Otherwise it does not exist for them, and they are not told why.

Details: [`backend/docs/features/007_products.md`](backend/docs/features/007_products.md).

## 8. Cart and Checkout

The cart can hold products from **multiple sellers**:

```
Cart
 ├── Seller A
 │     ├── Product A
 │     └── Product B
 └── Seller B
       └── Product C
```

Checkout produces **one parent order**. The backend:

1. Re-reads every cart item's product from the database. It **MUST NOT** trust prices, totals, or seller IDs from the client.
2. Validates each product: it exists, is purchasable, and belongs to an operational seller. It also validates quantity. Inventory and stock rules are **Open** (`K3`).
3. **Groups the items by seller.**
4. Creates one `Order` for the buyer, with payment still outstanding.
5. For each seller in the group, creates one `SellerOrder`, **resolves and snapshots that seller's applicable commercial terms** ([§10](#10-seller-plans-subscriptions-and-commission), [§11](#11-historical-correctness-and-snapshots)), and computes the seller subtotal and financial breakdown.
6. Creates an `OrderItem` per line, with its **product snapshot**.
7. Computes the order totals from the persisted seller orders and items.

Steps 4 to 7 MUST happen in **one database transaction**: either the whole order exists, or none of it does.

The buyer then **initiates payment** for the order ([§12](#12-payments-and-gateway-integration)). SellerOrders are **not released to sellers for fulfillment** until the payment is confirmed `Paid` ([§9.3](#93-status-at-two-levels)).

The buyer experience is **one marketplace checkout**, unless a later business rule explicitly says otherwise.

## 9. Orders: Order → SellerOrder → OrderItem

### 9.1 Structure

```
Buyer
  │
  └── Order
        ├── SellerOrder
        │     ├── Seller
        │     └── OrderItem
        │            └── Product (reference; snapshot is authoritative)
        ├── SellerOrder
        │     ├── Seller
        │     └── OrderItem
        └── SellerOrder
```

### 9.2 Responsibilities

**Order** is the buyer's complete checkout. It owns:

- the buyer, order number, currency, and order-level totals, which are derived from its seller orders plus any order-level charges whose rules are still **Open** (delivery `O6`, discounts `C8`);
- the **overall** order status, derived from the seller orders ([§9.3](#93-status-at-two-levels));
- its relationship to payment(s). Whether the order's payment condition is satisfied comes from the payments module.

Seller-specific fulfillment and financial data **MUST NOT** be stored only on the parent order.

**SellerOrder** is the portion of the checkout belonging to **one seller**. Each order has one SellerOrder per distinct seller. It owns:

- the seller-specific status and fulfillment lifecycle;
- the seller subtotal;
- the **commercial-terms snapshot** and the seller financial breakdown (commission rate, commission amount, seller amount, MUHUZE amount, plan/subscription reference);
- seller-specific rejection and cancellation, where allowed.

**OrderItem** is one purchased product and its quantity, within one SellerOrder. It owns:

- a reference to the product;
- a **purchase-time snapshot**: product name, product identifier, unit price, currency, and the selected attributes/variant information;
- the line total, computed from the snapshot.

### 9.3 Status at two levels

Seller portions of the same order move **independently**:

```
Order #10001
  Seller A → Delivered
  Seller B → Shipped
  Seller C → Accepted
```

**Release after payment.** A SellerOrder is created at checkout, but it enters the seller's fulfillment workflow only after the order's payment is confirmed `Paid`. Payment confirmation **activates** the SellerOrders. How "created but not yet released" is represented (a distinct state, or a release marker) is decided in the orders module. Whether sellers can *see* unreleased portions, and whether any non-prepaid flow such as cash on delivery exists, is **Open** (`O3`, `P8`).

**SellerOrder fulfillment lifecycle** (after release):

```
Pending ──► Accepted ──► Shipped ──► Delivered ──► Completed
   │            │
   ├──► Rejected (by the seller)
   └──► Cancelled ◄─┘ (by buyer/admin, where allowed)
```

- Every transition is enforced in the orders service, which checks the current state. An invalid transition fails with a specific error.
- Each transition is recorded with its timestamp and the actor who made it.
- All sellers in one order are **never** assumed to move through these states together.

**Parent Order status** describes the overall purchase. It is **derived** from its seller orders by **one** service function, and handlers never set it ad hoc. The exact derivation table (for example, what the parent shows when Seller A is `Delivered` and Seller B is `Rejected`) is **Open** (`O1`). Until it's confirmed:

- the derivation function is the only place this logic may live;
- the parent status is re-derived whenever any child status changes, in the same transaction.

**Payment status is a separate state machine** ([§12.2](#122-payment-status-lifecycle)). It is not mixed into order or fulfillment status.

## 10. Seller Plans, Subscriptions, and Commission

### 10.1 Configurable seller plans

MUHUZE supports **multiple seller subscription/commercial plans, configured by administrators**. Boolean flags such as `is_subscribed` or `is_partner` **MUST NOT** be the model. A flag can't carry the fee, the billing period, the rate, the validity, or history.

```
SellerPlan                     (admin-managed catalogue of plans)
  ├── name / code
  ├── subscription price + currency
  ├── billing period
  ├── commission rate
  ├── status (e.g. active / retired)
  └── other commercial rules / benefits
```

Example plans. **Illustrative only; not production values.**

```
STANDARD    fee = 0                    commission = 10%
BASIC       fee = 10,000 RWF / month   commission = 7%
BUSINESS    fee = 30,000 RWF / month   commission = 4%
PARTNER     fee = 100,000 RWF / month  commission = 0%
```

The real plan names, prices, billing periods, and rates are **Open** (`C1`–`C4`), and must stay admin-configurable.

### 10.2 Seller subscription assignment

A **SellerSubscription** assigns a plan to a seller for a period. A seller has a **history** of subscriptions, not one mutable field. For any seller and any moment, the system MUST be able to answer:

```
Which plan does this seller have?
When did it start?  When does it expire?
Is it active?
What commission rate applies?
What subscription fee applies?
```

Requirements:

- At most one subscription is **applicable** to a seller at a given moment. This must be guaranteed, not merely expected.
- Expired, cancelled, or not-yet-active subscriptions are **not** applicable.
- Several things are **Open**: whether a subscription keeps the plan's fee and rate as they were when it started, or follows later admin edits to the plan (`C5`); renewal (`C6`); grace periods (`C7`); mid-period plan changes and proration (`C9`); and whether activation waits for the subscription payment (`C10`). Whatever is decided, historical *transactions* are protected by the SellerOrder snapshot ([§11](#11-historical-correctness-and-snapshots)).

### 10.3 Commission precedence (confirmed)

```
Active applicable seller plan/subscription
        ↓
Use its configured commission rate        (may be 0%)

No applicable active plan/subscription
        ↓
Use the MUHUZE default seller commission rate
```

- This is resolved **per SellerOrder at the moment it is created**, by **one** resolver owned by `seller_plans` (e.g. `resolve_commercial_terms(seller, at)`). Orders call it, and nothing else computes a commission rate.
- The rate that is actually used, together with the plan/subscription reference (or "default rate"), is **persisted on the SellerOrder** and never recalculated ([§11](#11-historical-correctness-and-snapshots)).
- Whether `STANDARD` is a real plan that every seller is assigned, or simply means "no plan, so the default applies", is **Open** (`C11`). Either way, the precedence above holds.

### 10.4 Default commission rate

- MUHUZE has a **configurable default transaction commission rate** for sellers without an applicable active plan, e.g. 10% (example).
- It is **business configuration** owned by `seller_plans`, changed through an admin endpoint guarded by an explicit permission, and read only through the resolver.
- It **MUST NOT** be duplicated as a constant in services, schemas, tests, or the frontend.
- *Recommended:* store it as **effective-dated** configuration that records who changed it, when, and the old and new value, so commercial terms never need a deploy and every change is auditable.
- Changing the default **never** affects existing orders. Order A created at 10% stays at 10% after the default changes to 8%; Order B created afterwards uses 8%.
- The real default percentage is **Open** (`C4`).

### 10.5 Seller earnings

After a paid order, each seller's earning comes from **that SellerOrder's snapshotted rate**:

```
Seller with 5% commission                Seller on a 0% plan
  Product subtotal     100,000 RWF          Product subtotal     100,000 RWF
  MUHUZE commission      5,000 RWF          MUHUZE commission          0 RWF
  Seller earning        95,000 RWF          Seller earning       100,000 RWF
```

The 0% seller's subscription fee is accounted for **separately**, as subscription revenue. It is never deducted from or mixed into product-sale revenue. How delivery fees, discounts, taxes, and provider fees enter this calculation is **Open** (`C8`, `O6`, `T1`, `P6`).

### 10.6 MUHUZE revenue sources

```
MUHUZE Revenue
 ├── Transaction commission   (from SellerOrders, at the snapshotted rate)
 ├── Seller subscription      (from paid SellerSubscriptions)
 ├── Premium services
 └── Other future revenue
```

Each source is a **separate concept with its own records**, and records identify their source. Subscription payments MUST NOT be mixed into product-sale revenue. A seller on a 0% plan can produce subscription revenue while producing **zero** commission revenue. Platform revenue reporting aggregates across sources ([§16](#16-analytics)).

**Subscription flow:**

```
Seller chooses a plan
  ↓
SubscriptionPayment       (a Payment whose purpose is "subscription"; same provider abstraction, §12)
  ↓
Payment confirmed Paid
  ↓
SellerSubscription active
  ↓
SubscriptionRevenue recorded
```

Whether a subscription can be paid from the seller's wallet balance instead of an external payment is **Open** (`C12`).

## 11. Historical Correctness and Snapshots

**Historical financial and order records are never recalculated from current data.**

### 11.1 Commercial-terms snapshot

```
January    Seller has no plan; default = 5%   → Order #1   → 5% forever
February   Seller subscribes to a 0% plan
March                                         → Order #2   → 0%
```

Order #1 **remains a 5% commission transaction** after the seller's plan changes. It also stays at 5% if the default rate or the plan's own rate changes later.

So when a `SellerOrder` is created, it **MUST capture**:

```
commission rate
commission amount
seller amount
MUHUZE amount
plan / subscription reference (or "default rate") that was applied
```

Every later financial step (revenue, wallet, refunds, analytics) uses the **snapshot**, never the seller's current plan or the current default. A current plan **MUST NEVER** retroactively rewrite a historical financial record.

### 11.2 Product snapshot

```
Today      Product price = 100,000 RWF   → order placed at 100,000 RWF
Tomorrow   Seller changes price to 120,000 RWF
```

The order **stays at 100,000 RWF**. Each `OrderItem` preserves the purchase-time details:

```
product name
product identifier
unit price
currency
selected attributes / variant information
```

Order screens, invoices, refunds, revenue, and analytics read the snapshot. The live product row is only a reference, for things like "view this product".

## 12. Payments and Gateway Integration

MUHUZE MUST be able to operate **before** any automated payment gateway is integrated, and it MUST be ready to add gateways later without changing its financial domain. **The gateway is an integration mechanism, not the definition of MUHUZE's financial domain.**

### 12.1 Two payment phases, one financial domain

**Phase 1: manual/configured payment** (the initial operating mode)

```text
Buyer
→ MUHUZE configured payment destination     (buyer pays MUHUZE, following instructions)
→ Manual/administrative verification
→ Payment = Paid
→ Order processing
→ Seller earning
→ Seller wallet
→ Seller withdrawal
```

**Phase 2: automated payment gateway** (supplements or replaces Phase 1)

```text
Buyer
→ Payment Gateway
→ Provider verification/webhook
→ Payment = Paid
→ Order processing
→ Seller earning
→ Seller wallet
→ Seller withdrawal
```

Both phases MUST produce the **same internal state**, `Payment.status = Paid`, through the **same single confirmation service function**. Everything downstream (SellerOrder activation, revenue, seller earnings, wallets, withdrawals) **MUST NOT know or care** how the payment was verified. There is **no separate, simplified financial system for manual payments**. The only difference between the phases is how the payment *becomes verified*.

The unified flow:

```text
Buyer
  ↓
Create Order                         (Order + SellerOrders + snapshots, §8)
  ↓
Initiate Payment                     (internal Payment = Pending, destination/channel recorded)
  ↓
Buyer pays MUHUZE                    (Phase 1: to a configured destination · Phase 2: through a gateway)
  ↓
Confirmation arrives                 (Phase 1: buyer reference/proof · Phase 2: webhook/callback or status query)
  ↓
MUHUZE verifies                      (Phase 1: authorized admin · Phase 2: backend verification, §12.7)
  ↓
confirm_payment()  →  Payment = Paid           ← one function, both phases
  ↓
Order payment condition satisfied → SellerOrders activated
  ↓
Seller earnings + MUHUZE revenue recorded (§13)
```

### 12.2 Payment status lifecycle

Minimum states:

```
Pending ──► Paid ──► Refunded
   │
   └──► Failed
```

The model MUST be **extensible**. Add states only when a real flow needs them, for example:

- an "awaiting verification" state for Phase 1, once the buyer has submitted a reference or proof;
- `Processing`, `Cancelled`, `PartiallyRefunded`, and `Disputed`, once a provider or business rule requires them.

Don't implement every possible state ahead of time. Provider-specific statuses are **mapped** to internal states inside the provider adapter, and never leak into orders, revenue, or wallets.

An order can have several payment *attempts* (for example, a rejected reference followed by a valid one), but **at most one successful payment covers an order** unless split payments are approved (`P2`).

### 12.3 MUHUZE payment destinations

A **payment destination** is where the **buyer sends money to MUHUZE**. It MUST be an account or channel **controlled by MUHUZE or explicitly authorized by MUHUZE**.

```text
PaymentMethod                  (e.g. Mobile Money, Merchant Code, Bank Transfer, other approved type)
    │
    └── PaymentDestination
            ├── type
            ├── provider
            ├── account / reference     (phone number, merchant/MoMo code, bank account number, …)
            ├── registered_name
            ├── currency (where relevant)
            ├── status                  (active / inactive)
            ├── is_default
            └── configuration metadata
```

Examples. **Placeholders only; real values are admin-managed data, never in the repository:**

```text
Mobile Money      Provider: [configured provider]   Phone: [configured number]       Registered name: [configured name]
Merchant Code     Provider: [configured provider]   Merchant code: [configured code] Registered name: [configured name]
Bank Transfer     Bank: [configured bank]            Account: [configured account]    Account name: [configured name]
```

Rules:

- The supported payment methods and destinations are **configurable**, not hardcoded. The initial setup supports **one or more** configured default destinations.
- Authorized administrators, with an explicit permission, can **create, update, deactivate, set as default, and view** destinations.
- A destination that has been used by any payment is **deactivated, never deleted**.
- An **inactive** destination is never shown to buyers, and can never be the default.
- **Historical auditability:** each Payment records a **snapshot** of the destination it was paid to (type, provider, account/reference, registered name), as well as a link to the destination. If MUHUZE later changes its number or account, past payments still show where they were actually paid.
- **Exposure:** buyers see only the payment *instructions* they need (method, account/reference, registered name), and only for an order awaiting their payment. Full destination configuration and metadata is visible only to authorized administrators. No unrestricted endpoint lists payment configuration.

### 12.4 Payment provider abstraction

```
Payment                         ← internal MUHUZE record; source of truth for the marketplace
  ↓
Confirmation channel adapter    ← common interface; "manual" (Phase 1) and one adapter per gateway (Phase 2)
  ↓
ProviderTransaction             ← external references, raw responses, callback events, submitted evidence
```

- `Order`, `Revenue`, and `Wallet` depend on the internal **Payment** only, never on a provider or a channel.
- **Manual verification is one channel**, not a special case. Adding a gateway means adding an adapter. It never touches orders, revenue, or wallets.
- The internal Payment stores the external reference(s) needed to reconcile with the provider or the bank/mobile-money statement.
- The same abstraction serves **product-sale payments** and **subscription payments**. Each Payment records its **purpose**, so the two are never confused.
- Which gateway(s) will be integrated, and whether several run at the same time, is **Open** (`P1`, `P2`).

### 12.5 Phase 1: manual payment

```text
Buyer
  ↓
Creates Order
  ↓
MUHUZE shows the configured payment instructions (active destinations)
  ↓
Buyer pays MUHUZE outside the platform
  ↓
Buyer submits payment reference / proof, where required
  ↓
Authorized administrator verifies
  ↓
confirm_payment()  →  Payment = Paid
  ↓
Order becomes eligible for processing → SellerOrders activated
```

Before approving, the administrator verifies against the actual MUHUZE account statement:

```text
payment reference
amount (and currency)
date/time
payment destination it was sent to
buyer / order reference
transaction evidence (e.g. receipt, statement line)
```

- Submitted references are **validated server-side**: format, the payment belongs to this buyer and order, and the reference **hasn't already been used** to confirm another payment.
- Proof files, if they are required (`D6`), use private/authenticated storage (`core/storage.py`), the same as identity documents.
- Approval records **who** approved, **when**, and the evidence or reference relied on. Rejection records the reason. Both are auditable.
- How buyers submit references (`D5`), who may approve (`D7`), and whether approval needs one administrator or several (`D8`) are **Open**.

### 12.6 Phase 2: gateway payment

When a gateway is integrated, a **trusted, verified** confirmation may let the backend move the payment to `Paid` **automatically** and trigger order processing, through the same `confirm_payment()`. Manual approval remains possible wherever the business requires it (`P4`, `P5`).

### 12.7 Never trust the frontend, an unverified callback, or unchecked evidence

```
Frontend says "payment successful"   ≠   Payment = Paid
Gateway callback received            ≠   trusted
Buyer uploaded a screenshot          ≠   Payment = Paid
```

The backend is the source of truth. A payment becomes `Paid` only after verification:

- **Phase 1:** an authorized administrator checks the evidence against MUHUZE's actual received funds ([§12.5](#125-phase-1-manual-payment)).
- **Phase 2:** the backend verifies the confirmation according to the provider's integration requirements. Depending on what the provider supports, that means:
  - verifying the callback's **authenticity** (signature or secret);
  - and/or a server-to-server **status query**;
  - matching the **provider transaction reference**, **amount**, and **currency** against the internal Payment;
  - recording the raw response for audit.

A confirmation that fails verification or doesn't match does **not** mark the payment `Paid`. It is recorded and surfaced for review.

### 12.8 Idempotent confirmation

Providers may send the **same confirmation more than once**, administrators may click "approve" twice, and requests may be retried. Payment confirmation and all downstream financial processing **MUST be idempotent**:

```
Payment confirmation
        ↓
process once
        ↓
ignore / reconcile duplicate confirmation
```

A duplicate, whether from a gateway or a manual approval, MUST NOT cause:

```
Revenue created twice
Seller earning created twice
Wallet credited twice
Order processed twice
```

*Recommended mechanisms:*

- unique constraints on provider transaction/event references and on submitted manual payment references;
- a guarded state transition: only a not-yet-paid → `Paid` transition triggers processing, under a row lock or conditional update;
- database-level uniqueness on downstream records (one revenue record per SellerOrder, one earning wallet credit per SellerEarning);
- the whole confirmation effect (payment status, SellerOrder activation, revenue, wallet credits) in **one database transaction**.

### 12.9 External money vs. internal state

The external view ("the money arrived in MUHUZE's mobile-money/bank/gateway account") and MUHUZE's internal state (`Payment = Paid`, earnings, revenue) are **related but never conflated**. Reconciling external statements against internal Payments is an explicit, recurring operation in both phases. Its frequency and tooling are decided during payments implementation.

### 12.10 Payment security

- MUHUZE payment destinations are editable **only by authorized administrators**, with an explicit permission.
- Sensitive payment configuration is **never exposed through unrestricted APIs** ([§12.3](#123-muhuze-payment-destinations)).
- Secrets (provider keys, webhook secrets) and real account details are **never committed to git** ([§5.5](#55-configuration)).
- Payment references are **validated server-side**.
- Administrative payment approval is **auditable**: who approved, when, and on what evidence.
- **Duplicate confirmation is prevented** ([§12.8](#128-idempotent-confirmation)).
- Payment records are **never deleted** because a payment was reversed or refunded. Reversals are compensating records ([§13.7](#137-cancellations-refunds-and-reversals)).

## 13. Financial Architecture

> **The backend is the source of truth for all financial operations. The frontend never creates, calculates, credits, or directly modifies financial records.** It displays results and requests operations.

### 13.1 External money vs. internal accounting

These are two different flows, and the distinction is fundamental.

This is the [core money principle](#the-core-money-principle) in detail:

```text
The buyer pays MUHUZE
  → MUHUZE accounts for each seller's earning
  → the seller's wallet becomes available according to settlement rules
  → the seller withdraws
```

**External money movement** (real money crossing MUHUZE's boundary):

```
Buyer ──pays──► MUHUZE Payment Destination           (Phase 1: configured MoMo/merchant/bank · Phase 2: gateway)
                         …later…
MUHUZE ──payout──► Seller Payout Destination         (only via a completed Withdrawal)
```

**Internal accounting:**

```
Payment
  ↓
Order
  ↓
SellerOrder(s)            ← commercial-terms snapshot per seller
  ↓
RevenueTransaction(s)     ← one per SellerOrder
  ↓
SellerEarning + MUHUZE commission revenue
  ↓
WalletTransaction         ← the only way a wallet balance changes
  ↓
Seller Wallet             ← MUHUZE's recorded obligation to the seller
  ↓
Withdrawal                ← the only path to an external payout
```

A buyer pays **MUHUZE**, not the sellers. After confirmation, MUHUZE **accounts internally** for each seller's share and its own revenue. **A seller earning recorded in the wallet does not mean money has been transferred to the seller.** It is an obligation MUHUZE holds until a withdrawal is completed. This holds in both payment phases. Manual and gateway payments feed exactly the same internal accounting.

### 13.2 Distinct financial concepts

These concepts are related, and **none is the same as another**:

```
Order                 the buyer's purchase
Payment               money received for an order (or a subscription)
RevenueTransaction    accounting of one SellerOrder's sale
SellerEarning         what MUHUZE owes a seller for one SellerOrder
WalletTransaction     one auditable movement in a seller's wallet
Wallet                a seller's balances, backed by its WalletTransactions
Withdrawal            a request/process to pay available funds out
SubscriptionPayment   money received for a seller plan
SubscriptionRevenue   MUHUZE revenue recognized from a subscription
```

```
Payment              ≠  Revenue
Revenue              ≠  Seller Wallet
Seller Wallet        ≠  Withdrawal
Subscription Payment ≠  Product Sale Payment
MUHUZE Payment Destination ≠ Seller Payout Destination
Manually verified payment  =  gateway-confirmed payment   (identical downstream)
```

The separation is required for auditability and for provider independence.

### 13.3 Records and their responsibilities

| Record | Responsibility |
|---|---|
| **Order** | The buyer's whole checkout: totals and the derived overall status. |
| **SellerOrder** | One seller's portion: subtotal, fulfillment status, **commercial-terms snapshot and financial breakdown**. |
| **OrderItem** | A purchased line with its product snapshot. |
| **Payment** | Internal record of money received: purpose (order or subscription), amount, currency, confirmation channel (manual or gateway), destination snapshot, external reference(s), who/what confirmed it, status. |
| **PaymentDestination** | A MUHUZE-controlled receiving account/channel (admin-managed; deactivated, never deleted once used). |
| **ProviderTransaction** | The provider-side references, responses, and callback events for a Payment. |
| **RevenueTransaction** | Transaction accounting for **one SellerOrder**: gross amount, applied rate, MUHUZE commission, seller earning, currency, status, and links to its SellerOrder and Payment. Created **exactly once** per SellerOrder when its payment is confirmed, from the snapshot. |
| **SellerEarning** | The seller's entitlement from one SellerOrder. Whether it is its own table or part of the RevenueTransaction is an implementation choice, but it remains a distinct concept from the wallet credit it produces. |
| **SubscriptionRevenue** | MUHUZE revenue from a paid SellerSubscription. Separate from transaction revenue. |
| **ReferralCommission** | Eligible multi-level (Level 1/2/3) referral commissions. The funding rules are **Open** (`F1`). |
| **WalletTransaction** | An append-only wallet movement that references its source record. |
| **Wallet** | A seller's balances (e.g. pending, available, total earned, total withdrawn), changed **only** through WalletTransactions. |
| **Withdrawal** | A controlled movement of available funds out of the platform, to a snapshotted seller payout destination, with its own lifecycle ([§13.8](#138-withdrawals)). |
| **SellerPayoutDestination** | Where one seller receives withdrawals. Never a MUHUZE payment destination. |

### 13.4 Multi-seller payment example

Illustrative rates only.

```
Order #1001 total = 100,000 RWF   →   one Payment of 100,000 RWF to MUHUZE

SellerOrder A (Seller A, no plan → default snapshot 10%)
  subtotal            70,000
  commission (10%)     7,000   → MUHUZE transaction commission revenue
  seller earning      63,000   → Seller A wallet, pending

SellerOrder B (Seller B, PARTNER plan snapshot 0%)
  subtotal            30,000
  commission (0%)          0
  seller earning      30,000   → Seller B wallet, pending

Check: 63,000 + 7,000 + 30,000 + 0 = 100,000 = Payment amount
```

Each seller's breakdown is **independently traceable**: Payment → SellerOrder → RevenueTransaction / SellerEarning → WalletTransaction. Seller B's subscription fee is a separate SubscriptionPayment and SubscriptionRevenue, and isn't part of this order. Delivery fees, discounts, taxes, and provider fees MUST NOT be added implicitly until their rules are decided.

### 13.5 Seller wallet

Every seller has a wallet: an **auditable accounting balance inside MUHUZE**.

```
Seller
  └── Wallet
        ├── pending balance     (earned, not yet settled; cannot be withdrawn)
        ├── available balance   (settled; can be withdrawn)
        ├── total earned
        └── total withdrawn
```

- The wallet MUST NOT be a mutable number without history: `Seller → Wallet → WalletTransaction(s)`.
- Every movement is a WalletTransaction referencing its source. Examples: seller earning, settlement (pending → available), refund reversal, withdrawal, withdrawal reversal, administrative adjustment (permissioned, with a reason), referral commission, and other approved movements.
- Balances change **only** through WalletTransactions written by backend services, and always reconcile with them. No endpoint lets a client set or increase a balance.
- The final fields and the currency structure are decided during wallet design (`W7`). Settle the shape up front; the prototype had to reconcile legacy top-level balances against a per-currency structure, and that must not happen again.

### 13.6 Settlement: pending vs. available

```
Order Paid
   ↓
Seller earning recorded            → pending balance
   ↓
SellerOrder reaches the required completion/settlement state
   ↓
Settlement                         → available balance
   ↓
Seller requests withdrawal
   ↓
Withdrawal processing
   ↓
Withdrawal completed               → external payout
```

- **Pending and available are distinct.** A seller **MUST NOT** withdraw pending funds.
- Settlement is performed by **one** service rule. The triggering state and any holding period are **Open** and must remain configurable (`W1`, `W2`).

### 13.7 Cancellations, refunds, and reversals

The financial architecture must support:

```
successful purchase
cancellation (whole order)
seller rejection / partial seller cancellation (one SellerOrder), where applicable
refund (full, and partial if approved)
financial reversal
withdrawal reversal (failed payout)
```

Rules:

- **Financial records are never deleted or edited to "undo" them.** A reversal is a **new, compensating record** that references the original. History stays auditable.
- Every refund or reversal is **traceable** to its originating Order, SellerOrder, Payment, RevenueTransaction, and WalletTransaction(s).
- A reversal reverses exactly what was recorded, using the **snapshotted** amounts. It adjusts the seller wallet and MUHUZE revenue **correctly and once**.
- Cancelling one SellerOrder affects only that seller's portion, and the parent order status is re-derived.
- Operations are **idempotent**. Retrying a refund or reversal must not reverse twice.

Refund responsibility (`R1`), partial refunds (`R2`), refunds after funds have become available or been withdrawn (`R3`), and chargebacks/disputes (`R4`) are **Open**.

### 13.8 Withdrawals

A seller can request a withdrawal **from their available balance**, subject to:

- sufficient **available** balance (never pending);
- an **admin-approved seller** ([§15](#15-seller-verification-gates-withdrawals));
- withdrawal rules, **fees**, and **minimum/maximum limits** (`W3`–`W5`);
- a valid **seller payout destination** (below);
- administrative or automated review requirements (`W6`).

**Seller payout destinations.** A seller registers where they want to **receive** withdrawals:

```text
SellerPayoutDestination        (belongs to one seller)
  Mobile Money   → provider, phone number, registered account name
  Bank           → bank, account number, account name
```

- A payout destination is **completely separate** from MUHUZE's payment destinations ([§12.3](#123-muhuze-payment-destinations)). Buyer-payment configuration is **never** used as a seller's withdrawal account, and a seller's payout account is never shown to buyers as a place to pay.
- Payout destinations belong to the seller. Only that seller (ownership check) and authorized administrators can manage or view them, subject to verification rules. Whether a destination's registered name must match the seller's verified identity, and whether new or changed destinations need approval or a cooling-off period, are **Open** (`W9`).
- Each Withdrawal records a **snapshot** of the payout destination it was paid to, so later edits never rewrite where past payouts went. A destination used by a withdrawal is deactivated, never deleted.

Lifecycle, at minimum:

```
Pending ──► Processing ──► Completed
   │             │
   ├──► Rejected └──► Failed
   └──► Cancelled (by the seller, if allowed)
```

- Requesting a withdrawal **reserves** the amount through a WalletTransaction, so the same funds can't be withdrawn twice.
- A rejected, failed, or cancelled withdrawal returns the funds through a **compensating** WalletTransaction, never through an edit.
- Every withdrawal creates auditable wallet and financial records. Payout providers are **Open** (`W8`).

## 14. Financial Invariants

These are **engineering invariants**. Each one is a testable requirement and should map to at least one automated test.

1. **No duplicate revenue.** A payment never creates revenue twice. There is one revenue record per SellerOrder, enforced in the database.
2. **Idempotent confirmation.** Processing the same payment confirmation more than once has the same effect as processing it once.
3. **No duplicate wallet credit.** A seller never receives the same earning, refund, or reversal credit twice.
4. **Historical immutability.** Historical transactions don't change when seller plans, plan rates, the default rate, or product prices change.
5. **Plan precedence.** An active applicable seller plan takes precedence over the default commission rate.
6. **Default fallback.** A seller without an applicable plan uses the configured MUHUZE default commission, read from configuration and never from a constant.
7. **Revenue separation.** Subscription revenue is separate from transaction commission revenue.
8. **Ledger-backed wallets.** Seller wallet balances are backed by, and reconcile with, their WalletTransactions.
9. **No client-side money.** Frontend requests never directly change wallet balances, and never supply authoritative prices, amounts, or payment status.
10. **Available funds only.** Withdrawals only use available seller funds, never pending ones, and never more than the available balance.
11. **Traceability.** Refunds and reversals reference their originating transactions.
12. **Append-only history.** Financial records are never deleted or edited to reverse a transaction. Reversals are compensating records.
13. **Multi-seller reconciliation.** A single multi-seller payment reconciles exactly with all of its seller-specific records: `Σ (seller earning + MUHUZE commission + explicitly defined deductions) = payment amount`.
14. **External ≠ internal.** Provider state and internal MUHUZE financial state are linked by references and reconciled, never conflated.
15. **Safe callbacks.** Provider callbacks/webhooks can be repeated safely without duplicate financial effects.
16. **Verified payment only.** A payment becomes `Paid` only through the confirmation service, after verification by a gateway or by a permissioned administrator. A frontend claim, an unverified callback, or unchecked buyer evidence never does it.
17. **Payment integrity.** A paid payment's amount and currency match what the provider actually charged.
18. **Reproducible totals.** Order totals can be reproduced from persisted snapshots: OrderItems → SellerOrders → Order.
19. **Seller approval gate.** Only an admin-approved seller can list products or sell, and no withdrawal is created for a seller whose application isn't approved.
20. **Exact arithmetic.** Money uses decimal arithmetic with an explicit, documented rounding rule. The rule itself is **Open** (`C13`).
21. **Channel-independent processing.** A manually verified payment and a gateway-confirmed payment produce identical downstream records (SellerOrder activation, revenue, earnings, wallet transactions).
22. **Destination history.** A payment keeps the destination details it was actually paid to, even after the destination changes or is deactivated. A withdrawal keeps its payout destination in the same way. Used destinations are never deleted.
23. **Separate destinations.** A MUHUZE payment destination is never used as a seller payout destination, and vice versa.
24. **Single-use references.** One external payment reference can never confirm more than one payment.

## 15. Seller Verification Gates Withdrawals

**Decided 2026-10-05 (`S1`): a seller is verified and approved by an admin *before* selling.** This replaces the earlier "sell first, verify before withdrawing" rule.

```
Register account → Apply as seller (business info + identity documents) → Admin approves → Sell → Earn → Withdraw
```

- An account **cannot list products or sell** until its seller application has been **approved by an admin**, who reviews the identity documents.
- Verification therefore happens **once, at onboarding**. There is no separate "verify later" step before the first withdrawal.
- A withdrawal still **MUST** come from an approved seller. A request from a seller whose application isn't approved is rejected with `SELLER_VERIFICATION_REQUIRED`. Such a seller normally has no earnings, but the gate stays as a safety check.
- Seller status never affects the account's ability to log in or buy.

**The application covers** (decided 2026-10-06, `S3`–`S7`):

- **Business information:** shop name, description, and a business phone number.
- **Identity:** one document (national ID, passport, or driving license), its number, and photos of the front and back (a passport needs the front only). Stored privately; the number is visible to reviewing admins only. No selfie is required.
- **Business documents:** a business registration certificate and a TIN certificate are **optional**. A seller without a registered business can still apply.
- **Location:** exactly one per seller. The address is required (province, district, sector; cell and village optional). GPS coordinates are optional, captured from the device or a pin the seller places.
- **Review trail:** every status change is recorded with who made it, when, and why.

**Seller lifecycle** (carried forward from the previous implementation, detailed in the sellers feature doc when it's built): `draft → pending_review → active`, with `rejected` (editable, can resubmit), `suspended` (by an admin), and `deactivated` (by the seller, reversible).

**Review rules (decided 2026-10-06):**

- The application can be edited only while it is a draft or after a rejection. A rejection carries a reason the seller sees, and the seller fixes and resubmits the *same* application.
- Staff cannot approve or reject their own application.
- Approval makes the seller `active` and gives the account the `seller` role. The role records "was approved once" and is not removed by suspension; whether a seller may trade *now* is always the seller's status.
- Documents are JPEG, PNG, or PDF up to 5 MB, stored privately and opened only through links that expire after 5 minutes.
- Every status change is kept in a history: who, when, and why.

Details: [`backend/docs/features/004_sellers.md`](backend/docs/features/004_sellers.md).

**Still open:** whether a `suspended` or `deactivated` seller can withdraw money already earned (`S2`), whether an approved seller can change business details and how (`S8`), plus real phone OTP verification and the admin review screens in the frontend.

## 16. Analytics

Analytics come in two **distinct** audiences. Both are **read-only** views computed from the underlying financial and order records. The `analytics` module never writes financial data.

### 16.1 Seller analytics

Each seller eventually sees their own metrics, for example:

```
Total sales              Total orders            Gross merchandise value
MUHUZE commission        Seller earnings         Pending earnings
Available balance        Total withdrawn         Refunds
Adjustments              Subscription payments
```

A seller sees **only their own** data, enforced by the ownership check.

### 16.2 Platform (MUHUZE) analytics

Administrators eventually see platform-level metrics, for example:

```
Total sales              Total orders             Total transaction volume
Total MUHUZE commission  Subscription revenue     Total seller earnings
Pending seller liabilities (owed to sellers, not yet withdrawn)
Withdrawals              Refunds
Revenue by plan          Revenue by seller        Revenue by category
```

These require a specific permission.

### 16.3 Rules

- Metrics are **derived from auditable source records** (SellerOrders, RevenueTransactions, SubscriptionRevenue, WalletTransactions, Withdrawals). They are not kept as many independently updated counters.
- If aggregates are cached or pre-computed for performance, they MUST be **rebuildable** from the source records and are never the source of truth.
- Analytics use **snapshotted** values (rate, price, category at the time of sale), so historical reports don't shift when current data changes.
- The exact metric definitions (e.g. whether "total sales" is net of refunds) and reporting periods are **Open** (`A1`).

## 17. Implementation Roadmap

The modules are built in **dependency order**. Each step relies on relationships that must already be settled:

| # | Module | Why it comes here |
|---|---|---|
| 1 | **Auth / Users** | Identity, sessions, and RBAC. Every later authorization check depends on it. |
| 2 | **Sellers / Seller verification** | Products, plans, wallets, and withdrawals all hang off `Seller`. Admin approval of the seller application gates selling and withdrawing. |
| 3 | **Categories** | A product must be placed in one of its seller's own categories. |
| 4 | **Product attributes** (AttributeDefinitions) | Product validation needs the category's attribute contract. |
| 5 | **Products** | Seller-owned products with validated attribute values. Ownership checks are proven here first. |
| 6 | **Seller plans** (plans, subscription assignment, default rate, commission resolver) | Must exist **before orders**, because each SellerOrder snapshots the applicable terms when it is created. Subscription *billing* is completed after step 9. |
| 7 | **Cart** | Multi-seller cart over real products. |
| 8 | **Orders** | Order → SellerOrder → OrderItem, snapshots, two-level status, release-after-payment. |
| 9 | **Payments** | **Phase 1 first:** internal Payment record, status machine, MUHUZE payment destinations, payment instructions, reference/proof submission, permissioned manual approval, and the single idempotent `confirm_payment()`, built behind the channel abstraction. Subscription payments are wired here. **Phase 2** (the first gateway adapter) comes once a provider is chosen (`P1`) and requires no change downstream. |
| 10 | **Revenue accounting** | Per-SellerOrder revenue and earnings from snapshots, plus subscription revenue. |
| 11 | **Wallets** | Ledger-backed balances; pending/available settlement. |
| 12 | **Withdrawals** | Needs wallets plus the seller approval gate. Includes seller payout destinations. |
| 13 | **Analytics** | Read-only views over settled financial records (seller and platform). |
| 14 | **Referrals** | Builds on settled revenue rules. |
| 15 | **Notifications** | Reacts to events from the modules above. |
| 16 | **Premium services** | An additional revenue source on top of a working core. |
| 17 | **Admin** | Consolidated operations over all of the above. Admin endpoints for each module may be built alongside that module. |

MUHUZE becomes **fully operational on Phase 1** (configured destinations plus manual verification) once steps 1 to 12 are done. No gateway is required to launch the marketplace.

**Payment, revenue, and wallet logic MUST NOT be built before the seller, plan, and order relationships (steps 2 to 8) are defined and implemented.** Building money flows on an unsettled order model is how double-crediting and unreconcilable records happen.

Before each module is implemented, resolve the [Open Business Decisions](#20-open-business-decisions) that block it, and write its feature doc (`backend/docs/features/NNN_<feature>.md`) and database doc.

## 18. Testing Requirements

These scenarios MUST become **automated backend tests**. Every financial test asserts the **persisted database records**, not only the API responses.

**Single seller**

```
Buyer → Product → Seller → Payment → Revenue → Wallet → Withdrawal
```

**Multi-seller payment**

```
Buyer purchases products from Seller A + Seller B
→ one checkout, one payment, one parent Order
→ two SellerOrders
→ correct financial allocation per seller
→ correct seller earnings and wallets
→ Σ breakdowns = payment amount
```

**Default commission**

```
Seller has no active plan
→ product sold
→ default commission applied (from configuration)
→ correct MUHUZE revenue and seller earning
```

**Subscription plan commission**

```
Seller subscribes to a plan with a configured commission
→ product sold
→ plan commission applied
```

**Zero-commission plan**

```
Seller subscribes to a 0% plan
→ product sold
→ MUHUZE transaction commission = 0
→ seller receives the full applicable seller amount
→ subscription revenue recorded separately
```

**Plan change**

```
Order created under Plan A
→ seller changes to Plan B
→ existing order keeps Plan A terms
→ new order uses Plan B terms
```

**Default rate change**

```
Default = 10% → Order A uses 10%
Admin changes default to 8%
→ Order B uses 8%
→ Order A remains 10%
```

**Payment gateway confirmation (Phase 2)**

```
Order created → payment initiated → gateway confirms → backend verifies
→ Payment = Paid → SellerOrders released → revenue and earnings recorded
```

**Unverified confirmation**

```
Frontend reports success / callback fails verification / amount mismatch
→ Payment stays not Paid → no financial effects
```

**Duplicate gateway confirmation**

```
Gateway sends the same confirmation twice
→ first one processes
→ second one produces no duplicate revenue, earnings, wallet credits, or order processing
```

**Payment destination management**

```
Authorized admin creates a MUHUZE payment destination → succeeds
Unauthorized user modifies a payment destination      → rejected
Inactive destination → never presented to buyers, cannot be the default
Destination used by a payment → can be deactivated, cannot be deleted
```

**Manual payment (Phase 1)**

```
Order created → payment instructions show only active destinations
→ Payment Pending → buyer submits reference/proof → admin verifies → Payment = Paid
→ approval records who and when
Admin without permission → cannot approve
Reference already used for another payment → rejected
```

**Duplicate manual confirmation**

```
Admin approves the same payment twice (or two admins concurrently)
→ no duplicate revenue, earnings, wallet credits, or order processing
```

**Manual = gateway downstream**

```
Same order paid via manual verification vs. via gateway confirmation
→ identical SellerOrder activation, revenue, earnings, and wallet records
```

**Destination change**

```
Payment made to destination X → admin changes/deactivates X
→ historical payment still shows X's details at the time of payment
```

**Seller payout destination**

```
Seller registers payout destination → stored against that seller only
Seller A reads/changes Seller B's payout destination → rejected
Payout destination ≠ MUHUZE payment destination (never interchangeable)
Withdrawal → snapshot of the payout destination retained
```

**Withdrawal**

```
Seller has only pending funds → withdrawal rejected
Seller whose application isn't approved → cannot list products; withdrawal rejected (SELLER_VERIFICATION_REQUIRED)
Approved seller with available funds → accepted → wallet transaction created
→ tracked through its lifecycle; a failed payout returns funds via a compensating transaction
```

**Refund**

```
Paid order → refund
→ original financial records retained
→ reversal/refund records created and linked
→ seller wallet and MUHUZE revenue adjusted correctly
→ retry is idempotent, no duplicate credit
```

**Partial seller cancellation** (once the rules are decided)

```
Multi-seller order → one SellerOrder rejected/cancelled
→ only that seller's portion reversed; others unaffected; parent status re-derived
```

**Historical product price**

```
Order placed → seller changes product price
→ order, revenue, refunds, and analytics still use the purchase-time price
```

**Unauthorized access**

```
Seller A attempts to modify Seller B's product → rejected
Seller A requests Seller B's analytics → rejected
```

## 19. Pre-Launch Checklist

A successful build does **not** mean the platform is ready to launch. The bar is the complete financial lifecycle, proven end to end, including cancellation, refund, and reversal.

- [ ] End-to-end marketplace testing with controlled buyer, seller, and referrer accounts, exercising every SellerOrder status and the parent-order derivation.
- [ ] Multi-seller checkout: one order, one payment, multiple SellerOrders, correct per-seller breakdowns.
- [ ] Phase 1 operation: real MUHUZE payment destinations configured by an admin (not in the repo), payment instructions shown correctly, manual verification against real statements, approvals audited.
- [ ] Payment confirmation: manual path (and the gateway path, once one exists), duplicate and invalid confirmations.
- [ ] Payment → revenue: exactly one revenue record per SellerOrder.
- [ ] Plans: default vs. plan commission, plan changes, and default-rate changes, all verified against snapshots. Subscription revenue kept separate.
- [ ] Seller earnings → wallet: breakdown math, pending → available settlement.
- [ ] Referral commission testing: eligibility and Level 1/2/3 calculations under controlled transactions.
- [ ] Refund/reversal testing: compensating records, traceability, no double-crediting.
- [ ] Withdrawal testing: seller approval gate, available-only funds, limits, fees, lifecycle, failed-payout reversal.
- [ ] Provider reconciliation: internal Payments match the provider's records.
- [ ] Analytics: seller and platform figures reconcile with source records.
- [ ] Security audit: JWT protection, RBAC plus ownership checks, callback authenticity, unauthorized access, token handling on sensitive endpoints.
- [ ] Server-side validation of prices, quantities, IDs, currencies, and amounts.
- [ ] Production configuration: real database, URLs, CORS, secrets, and provider credentials, with no localhost defaults.
- [ ] Logging that makes financial failures traceable without leaking sensitive data.
- [ ] UI/UX pass: desktop and mobile, loading/empty/error states, notifications, forms, navigation.
- [ ] Business and legal readiness: marketplace, seller, privacy, terms, refund, subscription, and withdrawal policies.
- [ ] Final acceptance run, as one controlled scenario: registration → subscription → multi-seller purchase → completion → settlement → referral → withdrawal.

**Recommended real test:** Buyer A buys known-price products from Seller B (no plan, default rate) and Seller C (0% plan, paid subscription) in one checkout, with Referrer D. Complete a verified payment and the seller workflows, then inspect every SellerOrder snapshot, RevenueTransaction, SubscriptionRevenue, referral commission, WalletTransaction, and Wallet balance before a controlled withdrawal. Repeat the scenario with a duplicate confirmation, a cancellation, a partial seller rejection, and a refund.

## 20. Open Business Decisions

**Decided** (kept here as a record; the rule itself lives in the section named):

| ID | Decision | Date | Where |
|---|---|---|---|
| S1 | Sellers are verified and **approved by an admin before selling**. | 2026-10-05 | [§15](#15-seller-verification-gates-withdrawals) |
| I1 | Authentication uses a short-lived **Bearer access token** plus a rotating **refresh token** (not cookies). | 2026-10-05 | [§5.4](#54-authorization-and-ownership) |
| I2 | Permissions are named **`<resource>.<action>` with a singular resource**, e.g. `product.create`. | 2026-10-05 | [§5.4](#54-authorization-and-ownership) |
| S3 | Business documents (registration certificate, TIN) are **optional** in a seller application; a seller without a registered business can still apply. | 2026-10-06 | [§15](#15-seller-verification-gates-withdrawals) |
| S4 | **No selfie** is required in a seller application. | 2026-10-06 | [§15](#15-seller-verification-gates-withdrawals) |
| S5 | The **identity document number is stored**, visible to reviewing admins only. | 2026-10-06 | [§15](#15-seller-verification-gates-withdrawals) |
| S6 | A seller's **address is required** (province, district, sector; cell and village optional); **GPS coordinates are optional**. | 2026-10-06 | [§15](#15-seller-verification-gates-withdrawals) |
| S7 | A seller has **exactly one location**. | 2026-10-06 | [§15](#15-seller-verification-gates-withdrawals) |
| K1 | **No product variants**: one product has one price. | 2026-10-07 | [§7.4](#74-product-rules) |
| K2 | Attribute values are stored as **typed rows** validated against the category; nothing inherits (categories are flat). | 2026-10-07 | [§7.3](#73-products-dont-all-have-the-same-structure) |
| K4 | **No admin approval** of new products; staff can hide one afterwards. | 2026-10-07 | [§7.4](#74-product-rules) |
| K8 | A category, attribute, or option that products use **cannot be deleted, only switched off**. | 2026-10-07 | [§7.4](#74-product-rules) |
| T2 | **One currency, RWF**, for now. Currency conversion and mixed-currency orders remain undecided. | 2026-10-07 | [§7.4](#74-product-rules) |
| K6 | Not applicable: categories are seller-owned, so there are no marketplace categories to restrict. | 2026-10-06 | [§7.2](#72-seller-owned-categories) |
| K7 | **Each seller creates and owns the categories of their own shop**, and defines their attributes. Categories are flat, and there is no shared marketplace tree. | 2026-10-06 | [§7.2](#72-seller-owned-categories) |
| X1 | Only **products for sale** for now; no rental or service listing types. | 2026-10-06 | [§7.2](#72-seller-owned-categories) |
| I4 | An account must **verify its email before it can log in**. | 2026-10-05 | [§5.4](#54-authorization-and-ownership) |
| I6 | The **`admin` role always holds every permission**, and the first admin account is created at startup from environment settings. | 2026-10-06 | [§5.4](#54-authorization-and-ownership) |
| I5 | Verification codes and password reset links are sent by **email over SMTP**. No email provider is chosen yet; any SMTP service works. | 2026-10-05 | [§5.4](#54-authorization-and-ownership) |

The items below are **not decided**. Code MUST NOT settle them implicitly. Record each decision here, and in the owning feature's doc, once it's made. Decisions are grouped and given IDs so the rest of the document can refer to them.

**Commercial: plans and commission**

| ID | Decision | Blocks |
|---|---|---|
| C1 | Exact subscription plans: names and benefits. | seller_plans |
| C2 | Exact subscription prices and currency. | seller_plans |
| C3 | Billing period: monthly, yearly, or both. | seller_plans, payments |
| C4 | Exact commission rate for each plan, and the **exact default commission percentage**. | seller_plans |
| C5 | Whether a subscription keeps the fee and rate it started with, or follows later admin edits to its plan. | seller_plans |
| C6 | Whether subscriptions **renew automatically**. | seller_plans, payments |
| C7 | **Grace period** after a subscription expires. | seller_plans |
| C8 | Commission base: before or after discounts? Does it include delivery? Who funds discounts and promotions? | orders, revenue |
| C9 | Mid-period plan upgrades and downgrades, and proration. | seller_plans |
| C10 | Whether a subscription activates only after its payment is confirmed. | seller_plans, payments |
| C11 | Whether `STANDARD` is an assigned plan or simply "no plan, so the default applies". | seller_plans |
| C12 | Whether subscriptions can be paid from the wallet balance. | seller_plans, wallets |
| C13 | Rounding rule for commission and split amounts, and where any remainder goes. | orders, revenue |

**Payments**

| ID | Decision | Blocks |
|---|---|---|
| P1 | **Which future payment gateway(s)** will be integrated (Phase 2). Airtel Money was used in the previous implementation; that is not a decision. | payments |
| P2 | Whether multiple gateways are supported **simultaneously**, and whether one order can be **split** across payments or providers. | payments |
| P3 | Payment retry and expiry rules for unpaid orders. | payments, orders |
| P4 | Whether manual confirmation remains available after a gateway is integrated, and for which cases. | payments |
| P5 | Whether trusted gateway confirmation always auto-approves the payment, or some cases still need review. | payments |
| P6 | Provider **transaction fees**: who absorbs them (MUHUZE, seller, buyer). | payments, revenue |
| P7 | Additional payment states needed by the chosen provider(s). | payments |
| P8 | Any non-prepaid flow, such as cash on delivery. | payments, orders |

**MUHUZE payment destinations and manual payment (Phase 1)**

Actual account details are **never** decided in this document. They go into admin-managed data once confirmed.

| ID | Decision | Blocks |
|---|---|---|
| D1 | Which **mobile-money providers** MUHUZE will use. | payments |
| D2 | Which **telephone numbers**, **merchant/MoMo codes**, **banks**, and **MUHUZE accounts** receive marketplace payments. | payments (configuration only) |
| D3 | Whether **multiple destinations** can be active at the same time. | payments |
| D4 | Whether a destination can be the **default for a specific currency**. | payments |
| D5 | **How buyers submit payment references** (form field, message, …). | payments |
| D6 | Whether **payment screenshots/proofs** are required. | payments |
| D7 | **Who** can manually approve payments. | payments, auth |
| D8 | Whether manual approval needs **one administrator or several** (maker-checker). | payments |

**Orders and fulfillment**

| ID | Decision | Blocks |
|---|---|---|
| O1 | Parent order **status derivation table** for mixed child states, and what triggers `Completed`. | orders |
| O2 | Whether a seller can **partially cancel individual items** within a SellerOrder. | orders, revenue |
| O3 | Whether sellers can see SellerOrders **before payment** is confirmed. | orders |
| O4 | Seller-specific fulfillment rules: handling times, auto-cancel on no response. | orders |
| O5 | Seller-managed vs. MUHUZE-managed delivery. | orders |
| O6 | **Delivery/shipping:** fee calculation, per seller or per order, who pays, who receives it. | cart, orders, revenue |

**Catalog**

| ID | Decision | Blocks |
|---|---|---|
| K3 | **Stock management** and **inventory reservation** (at cart, checkout, or payment; for how long). Products are built without stock; this must be decided and built **before orders**. | inventory, cart, orders |
| K5 | Whether a **shared catalog** (several sellers offering one canonical product) is ever needed. | products |
| K9 | Is **cross-shop browsing by kind of product** wanted (a short list of marketplace departments in addition to each seller's own categories)? Without it, buyers find products across shops by search only. | categories, products, search |

**Wallets and withdrawals**

| ID | Decision | Blocks |
|---|---|---|
| W1 | **Settlement period:** which SellerOrder state releases pending funds, and any holding period. | wallets |
| W2 | Whether sellers can withdraw **immediately after order completion**. | wallets, withdrawals |
| W3 | **Withdrawal fees.** | withdrawals |
| W4 | **Minimum** withdrawal amount. | withdrawals |
| W5 | **Maximum** withdrawal amount and frequency limits. | withdrawals |
| W6 | Whether withdrawals require **manual admin approval**, and whether some sellers get **automatic** processing. | withdrawals |
| W7 | Wallet field structure and supported currencies. | wallets |
| W8 | Supported **seller payout providers**. | withdrawals |
| W9 | **Seller payout destination rules:** must the registered name match the verified identity? Do new or changed destinations need approval or a cooling-off period? | withdrawals, seller_verification |

**Refunds and disputes**

| ID | Decision | Blocks |
|---|---|---|
| R1 | **Refund responsibility:** seller, MUHUZE, or shared. Is commission returned? | revenue, wallets |
| R2 | **Partial refunds.** | payments, revenue |
| R3 | Refunds after the seller's funds became available, or were already withdrawn. | wallets |
| R4 | **Chargebacks/disputes.** | payments, revenue |

**Tax and currency**

| ID | Decision | Blocks |
|---|---|---|
| T1 | **Tax/VAT** handling, and whether prices include tax. | products, orders, revenue |
| T3 | **Currency conversion** rules, and whether one order can mix currencies. Only RWF exists today (`T2`). | products, orders, wallets |

**Items from the frontend guide not yet confirmed in this spec**

These were described in the frontend project guide before the README became the single source of business rules. The frontend demo already shows some of them. Each one needs a decision: confirm it into the relevant section, change it, or drop it.

| ID | Decision | Blocks |
|---|---|---|
| X2 | **Buying flow per type.** In-app checkout ([§8](#8-cart-and-checkout)) is confirmed for sale products. Do rentals and services use a "contact the seller" flow, bookings, or checkout? | orders, payments |
| X3 | **Contact visibility tied to subscriptions.** Can an admin *require* a subscription from a seller (or exempt one), with the seller's contact info **withheld by the API** while the required subscription is inactive? How does this combine with the commission-based plans in [§10](#10-seller-plans-subscriptions-and-commission)? | seller_plans, sellers, products |
| X4 | **Admin/platform wallet.** Does MUHUZE itself get a wallet, or is platform income tracked only through revenue records ([§13.3](#133-records-and-their-responsibilities))? | wallets, revenue |
| X5 | **Referral earners.** Can *every* user, buyers included, earn referral commission when someone they referred **buys or sells**? If so, where are a buyer's earnings recorded: a wallet for every user, or a separate earnings balance? (See also `F1`.) | referrals, wallets |
| X6 | **Engagement features.** Are wishlist, view counts, usage counters (bought/rented/booked/contacted), and "popular/trending" sorting part of the product, and are they server-side? | products, analytics |
| X7 | **Languages.** English only, or also Kinyarwanda and French? | all user-facing text |

**Frontend ↔ backend integration**

| ID | Decision | Blocks |
|---|---|---|
| I3 | **Machine-readable error codes:** add an `error_code` field to the response envelope (needed for e.g. `SELLER_VERIFICATION_REQUIRED`, [§15](#15-seller-verification-gates-withdrawals)), and/or structured per-field validation errors? See `backend/docs/api/response-format.md`. | all endpoints, frontend forms |

**Sellers, referrals, premium, analytics**

| ID | Decision | Blocks |
|---|---|---|
| S2 | Can a `suspended` or `deactivated` seller withdraw earnings they already have? | sellers, withdrawals |
| S8 | Can an **approved seller change business details** (name, phone, location)? Freely, with a new review, or only through staff? Today it is not possible. | sellers |
| F1 | **Referral funding:** is referral commission paid out of MUHUZE's commission? What applies to 0%-plan sellers? Who is eligible? | referrals, revenue |
| M1 | Scope of **premium services**, and how they relate to seller plans. | premium |
| A1 | Exact **seller and platform analytics metrics**, their definitions, and reporting periods. | analytics |

## 21. Engineering Principles

These working rules apply to every feature, and to financial features above all:

- Change one financial flow at a time.
- Build the backend source-of-truth logic first. The frontend requests and displays; it never computes.
- Test with controlled accounts and known amounts.
- Verify the actual database records after every financial action. Never trust a UI number, or a provider's word, until the backend accounting is verified.
- Encode business rules in exactly one service function, and test them there.
- Keep git commits clear and recoverable.
- Move toward a public launch only after the end-to-end tests pass.

## 22. Getting Started

```bash
cd backend
uv sync                          # install dependencies
cp .env.example .env             # set DATABASE_URL and JWT_SECRET_KEY (both required);
                                 # a hosted Postgres URL (e.g. Neon) can be pasted as-is
uv run alembic upgrade head      # create/update the database tables
uv run fastapi dev app/main.py   # dev server → http://127.0.0.1:8000/docs
uv run ruff check .              # lint
uv run ruff format --check .     # formatting
```

From the repository root, `npm run dev:backend` starts the same app with `uvicorn --reload`.

The tests need their own PostgreSQL database, named with a `_test` suffix and set as `TEST_DATABASE_URL` in `backend/.env`. Its schema is dropped and rebuilt on every run. Run the backend test suite with:

```bash
cd backend && .venv/Scripts/python -m pytest -q
```

---

*Launch target: a controlled, tested, and financially consistent multi-seller marketplace, not merely a successful build.*
