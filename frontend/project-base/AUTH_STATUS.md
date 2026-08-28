# Muhuze Frontend Auth Status

## Project Overview

Muhuze is a multi-seller marketplace. Clients browse and purchase products, sellers manage products and earnings, and admins manage users, orders, payments, commissions, and seller payouts. The backend is FastAPI/Python; this frontend is Next.js, React, TypeScript, and JavaScript tooling. Frontend changes must not modify backend files.

## Implemented

- `app/lib/api/client.ts`: Axios client using `NEXT_PUBLIC_API_URL`.
- Access tokens are attached as Bearer tokens to API requests.
- Refresh tokens are exchanged through `/auth/refresh` after a single `401`, with concurrent refresh requests shared.
- Invalid sessions clear browser storage and the middleware session cookie.
- `app/services/auth.service.ts`: the frontend-only auth API service for register, login, restore, refresh support, authorization, and logout.
- `app/context/auth-context.tsx`: small React Context API exposing `user`, `loading`, `login`, `register`, `logout`, `hasRole`, and `hasPermission`.
- `middleware.ts`: redirects unauthenticated requests from `/dashboard` to `/login` when no session cookie exists.
- `/login` and `/register`: functional forms connected to the backend.
- Backend role `buyer` is intentionally presented as frontend role `client`; `seller` and `admin` remain unchanged.
- Dashboard role navigation is driven by authenticated authorization data.

## Backend Auth Contract Used

- `POST /api/v1/auth/register`: `{ email, phone?, password }`.
- `POST /api/v1/auth/login`: returns `{ access_token, refresh_token, token_type }`.
- `POST /api/v1/auth/refresh`: rotates the refresh token pair.
- `POST /api/v1/auth/logout`: revokes a refresh token.
- `GET /api/v1/auth/me/authorization`: returns `roles` and `permissions`.
- `GET /api/v1/users/me`: returns the authenticated account/profile.

## Backend Integration Position

Authentication foundation is integrated on the frontend. Seller and admin API work must follow the backend Swagger/docs contract. The mounted backend currently exposes auth, users, sellers, categories, brands, attributes, products, listings, and catalog. Orders, payments, revenue, wallets, withdrawals, referrals, and admin routers are not mounted yet.

## Current Position

The next frontend work is to add API-only services first, then connect seller product/listing workflows and admin review/curation screens. Existing dashboard demo data is not evidence that an API exists.

## Rules For Future AI Changes

- Frontend code only: do not edit `backend/` for frontend tasks.
- Use `app/lib/api/client.ts` for HTTP requests; do not create ad-hoc `fetch` or Axios instances.
- Each feature area gets an API-only service under `app/services/` before UI components call it.
- Use `useAuth()` for auth state; do not duplicate token or user state in components.
- Treat middleware as a session-presence gate. The backend remains the source of truth for JWT validity and permissions.
- Use the backend role name `buyer` only at the API boundary; display and route using frontend role `client`.
- Do not remove existing pages, routes, or demo data unless the task explicitly replaces them.
- Keep TypeScript strict and use real types. Do not use `any`.
- Do not commit `.env`, secrets, tokens, or `node_modules`.
