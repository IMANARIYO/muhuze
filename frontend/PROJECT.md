# Muhuze — Frontend Guide

This file is the guide for **frontend** work: the rules every frontend change must follow, the structure, the design direction, and the progress log. **Business rules live only in the root [`README.md`](../README.md).** Read both before starting any task, and update section 9 (Progress) after finishing one.

---

## 1. Overview

> **Business rules are not defined here.** What MUHUZE does — products, orders, payments, seller plans, commissions, wallets, withdrawals, referrals — is specified only in the root [`README.md`](../README.md), the single source of truth for business rules across the repository. This guide covers **how the frontend is built**. If a screen needs a business rule that the README doesn't confirm, don't invent it: add it to README §20 (Open Business Decisions) and ask.

- **Frontend only.** This folder is a React + TypeScript single-page app. All data comes from the **Python backend** (`../backend`) over HTTP. Nothing that must be trusted (prices, totals, commissions, permissions, balances, hidden contacts, payment status) is decided in the frontend. The frontend displays what the API returns and sends requests.
- **API contract:** every backend response uses one envelope, `{ success, data, message, status_code }`, plus an `X-Request-ID` header. See [`../backend/docs/api/response-format.md`](../backend/docs/api/response-format.md). The API client must unwrap `data` and surface `message` on errors.

---

## 2. Access control and layouts

These are UI rules. The roles, permissions, and ownership rules themselves are defined by the backend (README §5.4).

- **Roles are dynamic**: an admin can create new roles. **Permissions are a fixed, backend-defined list**; admins only assign them to roles.
- The UI therefore **checks permissions, never role names**. Write `can('<permission>')`, never `role === 'seller'`. A role created tomorrow must work without a code change. The permission naming convention is still open (README §20, `I2`).
- Hiding a button is never security. The API enforces every permission, and the UI only reflects it.

### Layout per kind of user

| User | Layout |
|---|---|
| Buyer (no management permissions) | Public storefront layout: top navigation only. **Never a sidebar/dashboard.** |
| Admin, seller, and any role with management permissions | **One shared dashboard** with one sidebar and one topbar. Sidebar items, pages, and actions are shown or hidden by permission. |

There is exactly one dashboard and one sidebar in the codebase, not one per role.

### Platform scope and own scope

Two kinds of permission decide what a dashboard user sees:

- `*.manage` / `wallet.view` — the whole platform (admin): every listing, every order, plans and rates, the platform wallet, users and roles.
- `*.own` — only what belongs to the user's shop (seller): `product.own`, `order.own`, `subscription.own`, `wallet.own`.

A sidebar link lists the permissions that open it (`permissions: ['product.manage', 'product.own']`). Pages shared by both scopes (Overview, Products, Orders) check the platform permission and otherwise narrow to `user.shop`.

### Order flow

1. A buyer checks out and gets an order reference. Nothing is paid in the app.
2. The buyer sends the money to the Muhuze account, outside the app, from the number they gave.
3. An admin sees every order and marks it **Payment received** (approved).
4. Only then do the sellers of the ordered items see the order, and its amount (minus commission on sale products) counts in their wallet.

---

## 3. Features

The features and their rules are listed in the root README. Building a screen for a feature means following the README's confirmed rules for it.

The demo UI built so far (section 9) also shows ideas that are **not yet confirmed** in the README: multiple product types (sale/rental/service), contact hiding tied to subscriptions, an admin wallet, referral earnings for every user, engagement counters, and languages. These are tracked in README §20 as `X1`–`X7`. Don't extend them further until they're decided, and change the UI to match whatever is decided.

UI principles that still apply whatever is decided:

- Build **one** product card and **one** product form, with sections that vary by product data, never several copies.
- Withheld data, such as a hidden contact, is **absent from the API response**. The UI shows a locked state when the field is missing, and never receives data only to hide it with CSS.
- Wallet screens show the ledger the backend returns. Recording an earning is not paying the seller (README §2, "The core money principle").

---

## 4. Rules (must be followed in every change)

### Performance — first priority
1. Lazy-load every route (`React.lazy`); a buyer must never download dashboard code.
2. Cache server data and avoid duplicate requests; paginate or infinite-scroll every list.
3. Lazy-load images with fixed dimensions (no layout shift); virtualize very long lists.
4. The **React Compiler is enabled** — do not add `useMemo` / `useCallback` / `React.memo` by hand unless a measured problem requires it.
5. Check bundle impact before adding a dependency. Prefer what is already installed.

### TypeScript
6. Real, precise types only. **No `any`**, no `as` casts to silence errors, no `@ts-ignore`.
7. Request-body and response types contain **only the fields actually used**. Derive variants with `Pick` / `Omit` instead of redefining.
8. No `enum` (the config enforces `erasableSyntaxOnly`) — use string-literal unions.
9. Use `import type` for type-only imports (`verbatimModuleSyntax` is on).

### Code
10. **Write only what is needed now.** No speculative files, folders, props, helpers or abstractions. No dead or commented-out code.
11. Keep code short and simple; the fastest readable solution wins.
12. **File size: aim for under 150 lines, hard limit 200.** When a file grows past that, split it into smaller components or hooks.
13. Reuse before writing: if two places need the same UI or logic, extract one reusable component/hook.

### UI
14. **shadcn/ui components are mandatory** for all UI primitives (button, input, dialog, table, sidebar…). Do not hand-build what shadcn provides.
15. **Tailwind only** for styling. No `.css` files except the global `src/index.css` (theme tokens), no inline `style`, no CSS-in-JS.
16. Colors and fonts come from theme tokens (`bg-primary`, `text-muted-foreground`) — never hard-coded hex values in components.
17. Every screen is responsive (mobile first) and handles loading, empty and error states.

### Structure
18. Related things live together. A folder owns its private parts in `_components`, `_hooks`, `_types`; only things used by **two or more** areas go to the global folders.
19. Access control is by **permission**, never by role name (see section 2).
20. **Pages fetch, components receive.** Server data is requested only in a page file (`pages/**/index.tsx`, `detail.tsx`) or a layout — never inside a reusable component. Reusable components (`_components`, `components/shared`) take their data through props and hold only interactive state. This is the Vite equivalent of "server-component page, `use client` components": this app is a client-rendered SPA, so there are no server components and `'use client'` has no effect here; the rule keeps the same separation so pages can move to server rendering later without rewriting components.

---

## 5. Folder structure

```
src/
├── main.tsx
├── App.tsx                  # providers + router only
├── index.css                # Tailwind + theme tokens (the only CSS file)
├── components/
│   ├── ui/                  # shadcn components (generated)
│   └── shared/              # global reusable components (used in 2+ areas)
├── layouts/
│   ├── PublicLayout.tsx     # buyer/storefront: topbar, no sidebar
│   └── DashboardLayout.tsx  # the one sidebar + topbar, permission-driven
├── pages/
│   ├── home/
│   ├── products/            # browse + product detail
│   ├── wishlist/
│   ├── auth/
│   └── dashboard/
│       ├── _components/     # used only inside dashboard
│       ├── products/
│       │   └── _components/
│       ├── subscriptions/
│       ├── referrals/
│       ├── wallet/
│       ├── users/
│       └── roles/
├── services/                # API calls, one file per resource
├── router.tsx               # lazy route table
├── hooks/                   # global hooks (e.g. useSession)
├── types/                   # global shared types (User, Product…)
└── lib/                     # api client, utils
```

Folders are created **only when the first file that belongs in them is written**. This tree is the target map, not something to scaffold in advance.

---

## 6. Tech stack

| Area | Choice | Status |
|---|---|---|
| Build / framework | Vite 8, React 19, TypeScript 6 | Installed |
| Compiler | React Compiler (babel preset) | Installed |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) | Installed |
| UI components | shadcn/ui | Installed |
| Routing | React Router | Installed |
| Server data / caching | TanStack Query | Installed |
| Forms | Native forms with React 19 actions (`FormData`); add Zod when API validation is needed | In use |
| Charts | Recharts through shadcn `chart` | Installed |
| Toasts / theme | Sonner, next-themes | Installed |
| Client state (auth session only) | Zustand | Proposed, add only if needed |

"Proposed" items are recommendations and are confirmed when first needed.

---

## 7. Design direction

Goal: attractive, professional, modern — it should feel like a trusted marketplace with the liveliness of a social app, and show innovation in both look and behaviour.

- **Fonts:** *Roboto* for everything (variable font, weights 100–900), with the system font as fallback. Large headings use the light weight (300) with a medium (500) phrase for emphasis; body and navigation use regular (400) at 14px.
- **Hero:** flat grey background, small uppercase spaced eyebrow, light headline, square dark uppercase button.
- **Colors** (defined once as theme tokens in `src/index.css`, with light and dark mode):
  - Primary — deep emerald/teal: trust, money, growth.
  - Accent — warm amber: calls to action, deals, highlights.
  - Neutrals — slate scale for text, borders, surfaces.
  - Semantic — green success, red destructive, amber warning.
- **Feel:** generous spacing, rounded cards, image-first product cards, subtle motion on hover and page transitions, skeleton loaders instead of spinners.
- **Buyer side** is visual and browsable; **dashboard side** is calm, dense and efficient.

Fonts and palette are a proposal and can be adjusted before the theme is implemented.

---

## 8. Open questions

Business questions (referrer earnings, referral funding, buying flow, languages, authentication method, permission list) have moved to README §20 (`X1`–`X7`, `I1`–`I3`, `F1`), so every team works from one list. Add **frontend-only** questions here.

---

## 9. Progress

### Done
- [x] Vite + React 19 + TypeScript project created
- [x] Tailwind CSS v4 installed and wired into Vite
- [x] React Compiler enabled
- [x] Project guide written (this file)
- [x] Starter template files removed
- [x] TypeScript `strict` enabled and `@/` path alias added
- [x] shadcn/ui initialised (Base UI style: use the `render` prop, not `asChild`)
- [x] Theme tokens in `src/index.css`: emerald primary, amber `highlight`, Roboto, light and dark
- [x] Router with lazy routes, `PublicLayout` and `DashboardLayout`
- [x] API client (`lib/api.ts`) and TanStack Query provider
- [x] `useSession` hook with `can(permission)`; permission-driven sidebar and topbar
- [x] Dashboard shell: grouped sidebar with user menu, topbar with dark-mode toggle and notifications, per-page permission guard
- [x] Dashboard pages on demo data: Overview (stats, revenue chart), Products, Subscriptions (rates, plans, sellers), Referrals, Wallet, Users, Roles & permissions
- [x] Orders: admin sees all and approves payment; sellers see their items from approved orders
- [x] Seller dashboard: overview with earnings chart, own products (add, edit, delete), My subscription (plans and subscribe request), My wallet (balance from approved orders)
- [x] Storefront seller collection: `/products?seller=`, linked from the seller card on a product page and from the "Shops" menu in the header
- [x] Dashboard building blocks in `pages/dashboard/_components`: `DataTable`, `FormDialog`, `RowActions`, `StatCard`, `StatusBadge`, `PageHeader`
- [x] Marketplace header: search, wishlist count, type links, trust highlights, profile menu (email, referral link, theme, dashboard)
- [x] Footer with brand, the same links as the header, and social links
- [x] Home page: animated 3D hero, tall category picture cards, trending panels, most-sold products carousel
- [x] Products: browse page (search + type filter) and detail page with locked seller contact
- [x] Hero: location search (`/products?location=`), statistics that count up in three seconds
- [x] Cart (saved in the browser): buy button on the detail page, header cart icon, `/cart` page
- [x] Checkout (`/checkout`): receiver, delivery address (province, district, sector, cell) and the number the buyer pays from; confirmation with an order reference
- [x] Route error screen (`pages/error.tsx`): reloads once when a page file is out of date, otherwise offers a reload
- [x] Wishlist (saved in the browser), view and usage counters on the detail page
- [x] Animation system in `src/index.css`: `animate-float`, `animate-blob`, `animate-rise`, `reveal` (scroll), `stagger`

### Temporary — remove when the backend is connected
- `lib/api.ts` returns the raw response body and throws `status statusText` on errors. It must unwrap the `{ success, data, message, status_code }` envelope and surface `message` once it calls the real backend.
- `services/auth.ts` returns a demo admin or a demo seller while `VITE_API_URL` is not set; the Admin / Seller switch in the dashboard topbar (`RoleSwitch`) swaps them and disappears once the API is connected.
- Permission names (`dashboard.view`, `product.manage`…) and the `/auth/me` endpoint are placeholders until the backend list is known.
- Dashboard pages keep their data in memory through `lib/demo-store.ts` (`_data.ts` files); changes are lost on reload. Replace each store with API queries and mutations.
- Dashboard listings are not linked to the storefront listings yet.
- The header "Shops" list comes from the demo listings; `GET /shops` is a placeholder endpoint.
- `services/products.demo.ts` supplies demo listings (Unsplash photos) while `VITE_API_URL` is not set.
- The wishlist and the cart are stored in `localStorage` (`lib/id-store.ts`) until backend endpoints exist.
- `services/orders.ts` adds checkout orders to the in-memory list in `services/orders.demo.ts` while `VITE_API_URL` is not set (lost on reload); `POST /orders` is a placeholder endpoint. Dashboard pages read that list directly.
- A seller is matched to listings, orders and subscriptions by shop name (`user.shop`); the backend should scope these by the signed-in user instead.
- Listing locations are demo towns; the location search matches the typed text, not real distance.
- Footer social links point to `#` until the real Muhuze accounts are known.
- The referral code (`DEMO2026`) comes from the demo user; the `/r/:code` landing route does not exist yet.
- Hero statistics (15K+ products…) and the floating chips are placeholder numbers.

### Next
- [ ] Auth pages (login, register) once the backend auth method is known
- [ ] Connect dashboard pages to the backend, one resource at a time
- [ ] Paying sellers out (settlements against a seller wallet)

### Later
- [ ] Referral registration through a shared link

### Change log
| Date | Change |
|---|---|
| 2026-10-01 | Project guide created; foundation and feature roadmap defined |
| 2026-10-01 | Foundation implemented: shadcn, theme, router, layouts, API client, session and permissions |
| 2026-10-01 | Buyer side redesigned: marketplace header, 3D animated hero, product browse, detail and wishlist |
| 2026-10-01 | Dashboard built: sidebar, topbar and seven working pages on demo data |
| 2026-10-04 | Business rules moved to the root README (single source of truth); this guide now covers frontend rules only. Unconfirmed business ideas tracked as README §20 `X1`–`X7`, `I1`–`I3` |
| 2026-10-05 | Header and footer reworked: highlights moved into the header, profile menu, social links; rule 20 added |
| 2026-10-05 | Hero location search and count-up statistics; cart with buy buttons, header icon and cart page |
| 2026-10-05 | Checkout with delivery details; payment happens outside the app |
| 2026-10-06 | Home referral banner replaced by a carousel of the most sold products |
| 2026-10-06 | Font changed to Roboto (Inter and Plus Jakarta Sans removed); hero and header restyled to the light editorial look |
| 2026-10-06 | Listings shown as panels of four pictures (`ProductGrid`); category picture cards on the home page; no zoom on product pictures |
| 2026-10-06 | Admin and seller dashboards: platform/own permissions, orders with admin approval, seller overview, subscription, wallet and storefront collection |
