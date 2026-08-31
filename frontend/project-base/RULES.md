# Muhuze Marketplace — Project Rules

## Purpose
Muhuze is an online marketplace platform with three user roles:
- **Seller**: Lists products (name, price, category, optional unit). Manages their product catalog and views earnings/commission payouts from admin.
- **Client**: Browses products, adds to cart, completes payment. Views order history and order status.
- **Admin**: Oversees all orders and payments. Sends commission payouts to sellers after deducting platform fee. Manages users and platform activity.

## Flow
1. Seller posts a product → visible to all clients
2. Client adds product to cart → completes payment
3. Admin sees payment notification + order → sends seller their share (price minus commission)
4. Seller sees payout in their earnings dashboard

## Tech Stack
- Next.js (App Router), TypeScript, Tailwind CSS
- No heavy client-side packages; prefer server components where possible
- Client components only when interactivity is required (`"use client"`)

## Frontend Rules

- This is the Next.js frontend. Backend code is Python/FastAPI and must not be changed for frontend work.
- Use Axios through `app/lib/api/client.ts` for all API calls.
- Add an API-only service under `app/services/` for each feature area before using that API in a component.
- Keep auth state in `app/context/auth-context.tsx` and access it with `useAuth()`.
- Dashboard routes are protected by `middleware.ts`; backend JWT validation and permissions remain authoritative.
- The backend role `buyer` maps to the frontend role `client`. Other roles are `seller` and `admin`.
- Keep pages server components by default; add `"use client"` only for forms, context, or browser APIs.
- Use strict TypeScript types. Do not use `any`.
- Do not remove existing routes or demo data without a specific requirement.
- Never commit `.env` files, secrets, tokens, or `node_modules`.

## File Structure
```
app/
  _components/
    public/          # Shared public-facing components (header, footer)
    ui/              # Reusable UI primitives (button, card, badge, input, avatar)
  (private)/
    _components/     # Dashboard-only components (sidebar, topbar, role-switcher)
    dashboard/
      _components/   # Page-level dashboard components
      page.tsx       # Role-based overview
      products/      # Seller: product management | Client: browse products
      orders/        # Client: order history | Admin: all orders
      cart/          # Client: cart & checkout
      payments/      # Admin: payment management & notifications
      earnings/      # Seller: earnings & payout history
      users/         # Admin: user management
      settings/
      profile/
    layout.tsx
  lib/
    types.ts         # All TypeScript types and interfaces
    data.ts          # Dummy data (products, orders, users, etc.)
    utils.ts         # Utility functions
  page.tsx           # Public landing page
  globals.css
  layout.tsx
```

## Coding Rules
- Use TypeScript with real types — no `any`
- Pages are server components by default; add `"use client"` only when needed
- Role-based navigation: one dashboard, sidebar/content changes per role
- Components inside a route folder go in `route/_components/`
- Shared dashboard components go in `(private)/_components/`
- Dummy data lives in `app/lib/data.ts` until backend API is ready
- No unnecessary `useEffect` — prefer derived state and server data patterns
- Keep UI consistent: use design tokens from `globals.css` (`--ink`, `--teal`, `--coral`, etc.)
- All navigation links and buttons must be functional (use dummy data where needed)
- Mobile responsive at all breakpoints

## Backend Source Of Truth

- Before integrating an API, inspect the mounted Swagger contract in `backend/app/main.py` and `backend/app/api/v1/router.py`.
- Read the owning module documentation under `backend/app/modules/**/docs/*.md` before designing its UI or request flow.
- The backend uses `router.py -> controller.py -> service.py -> repository.py`; the frontend must consume the router contract and must not reproduce backend business rules.
- Every backend response uses `{ status, message, data }`; unwrap and type `data` in the feature service.
- IDs are UUID strings in frontend types. Dates are UTC ISO strings.
- Public client shopping uses `GET /api/v1/catalog`; it must not use admin/seller `/products` rows as buyable offers.
- A buyable offer requires an active product, active variant, active seller, and active seller listing. Price and stock belong to the listing, not the product.
- Seller product flow is `POST /products` -> variants/images -> submit -> admin approval. Seller listing flow is `POST /listings` -> submit -> admin approval.
- Seller lifecycle is `draft -> pending_review -> active | rejected`, with documents required before submission. Seller role and seller status are different concepts.
- Admin-only API calls must be hidden or disabled unless `useAuth().hasRole("admin")` is true; backend authorization remains authoritative.
- The backend currently has no mounted orders, payments, revenue, wallets, withdrawals, referrals, or admin module APIs. Do not invent frontend API calls for them; keep placeholders clearly marked until Swagger exposes them.
- Do not change backend files while implementing frontend features unless the user explicitly requests a backend change.

## Swagger / OpenAPI Contract (attention on every integration)

The live Swagger UI is at `http://127.0.0.1:8000/docs` (dev). The OpenAPI JSON is at `/openapi.json`. Every integration must match the contract exactly:

- **Mounted routers** (from `backend/app/api/v1/router.py`): `auth`, `users`, `sellers`, `categories`, `brands`, `attributes`, `products`, `listings`, `catalog`. No other tags are mounted — do not call unmounted paths.
- **Response envelope**: every response is `{ status: "success"|"error", message: string, data: T|null }`. Always unwrap `data` in the service layer; never access it directly in components.
- **Auth**: `POST /auth/login` returns `{ access_token, refresh_token, token_type }`. Send `Authorization: Bearer <token>` on every protected endpoint. Token refresh is handled automatically by the Axios interceptor in `app/lib/api/client.ts`.
- **Seller status gate**: `Seller.status === "active"` is required to create products and listings. The `seller` RBAC role alone is not sufficient — always check seller status from `GET /sellers/me`.
- **Product ownership**: while `draft`/`pending_review`/`rejected`, only the creating seller or admin can edit. Once `active`, any active seller can add variants/images.
- **Listing states**: `draft → pending_review → active | rejected`. Additional: `suspended`, `out_of_stock`, `archived`. Price/stock can be updated on active listings via dedicated PATCH endpoints without re-review.
- **Document upload**: multipart/form-data with fields `document_type` and `file`. Required combination before seller submit: both `national_id_front` + `national_id_back`, OR `passport` alone, OR `driving_license` alone.
- **Admin actions on sellers**: `POST /sellers/{id}/approve|reject|suspend|reactivate` — each enforces the correct source state (409 on wrong state).
- **Admin actions on products**: `POST /products/{id}/approve|reject|archive`.
- **Admin actions on listings**: `POST /listings/{id}/approve|reject|suspend|reactivate`.
- **Categories/Brands/Attributes**: reads are public (no auth); writes are admin-only.
- **Catalog**: `GET /catalog` and `GET /catalog/products/{id}` are public, read-only, and only return fully-active rows (active product + active variant + active seller + active listing).
- **404 vs 403**: seller documents 404 on unauthorized access (KYC privacy). Product/listing ownership violations return 403.
- **IDs**: UUIDs everywhere. Never use integer IDs.
- **Pagination**: v1 has no pagination — all matching rows are returned. Filter params narrow results.

## Backend Documentation Index

- API overview and mounted tags: `backend/app/main.py`
- Router aggregation: `backend/app/api/v1/router.py`
- Auth and RBAC: `backend/app/modules/auth/docs/`
- Profiles: `backend/app/modules/users/docs/`
- Seller onboarding and documents: `backend/app/modules/sellers/docs/`
- Catalog and buyer storefront: no separate docs folder; see `backend/app/modules/catalog/`
- Products, variants, listings, and lifecycle: `backend/app/modules/products/docs/`
- Category hierarchy and admin CRUD: `backend/app/modules/categories/docs/`
- Scaffolded future finance/admin areas: inspect their docs before implementation; absence of a mounted router means no API integration is available yet.

## Test Credentials (backend `.env`)

These accounts are seeded at startup via `backend/app/core/bootstrap.py`:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@muhuze.com` | `AdminPassword123!` |
| Seller | `seller@muhuze.com` | `SellerPassword123!` |
| Client (buyer) | `client@muhuze.com` | `ClientPassword123!` |

Credentials are stored in `backend/.env` under `SUPER_ADMIN_EMAIL/PASSWORD`, `TEST_SELLER_EMAIL/PASSWORD`, `TEST_CLIENT_EMAIL/PASSWORD`. Never hardcode these in frontend code.
