# Muhuze v2 — Project Guide

This file is the single source of truth for the project: what we are building, the rules every change must follow, and the progress log. **Read it before starting any task, and update section 9 (Progress) after finishing one.**

---

## 1. Overview

Muhuze is a **social marketplace**: a platform where many people meet around products, the way they meet around posts on social media. Any seller can join and list something; any buyer can browse, save, and contact or buy; anyone can invite others and earn from it.

- **Frontend only.** This repository is a React + TypeScript single-page app. All data comes from a **Python backend over HTTP APIs**. No business logic that must be trusted (prices, commissions, permissions, hidden contacts) is decided in the frontend — the frontend only displays what the API returns and sends requests.
- **Three pillars:** multi-type products, subscriptions, referrals — plus wallets and social engagement features that tie them together.

---

## 2. Users, roles and permissions

- There is **one `User` model**. There are no separate admin / seller / buyer models.
- **Roles are dynamic.** Admin, seller and buyer are only the starting roles. An admin can create a new role at any time.
- **Permissions are predefined** (a fixed list provided by the backend, e.g. `product.create`, `subscription.manage`). An admin cannot invent permissions, only **assign** existing ones to a role.
- The UI must therefore **check permissions, never role names**. Write `can('product.create')`, never `role === 'seller'`. A role created tomorrow must work without a code change.

### Layout per kind of user

| User | Layout |
|---|---|
| Buyer (no management permissions) | Public storefront layout: top navigation only. **Never a sidebar/dashboard.** |
| Admin, seller, and any role with management permissions | **One shared dashboard** with one sidebar and one topbar. Sidebar items, pages and actions are shown or hidden by permission. |

There is exactly one dashboard and one sidebar in the codebase — not one per role.

---

## 3. Features

### 3.1 Multi-type products

Every listing has a **product type**, which changes its fields, its call to action and how the platform earns from it.

| Type | Examples | Buyer action | Platform earns via |
|---|---|---|---|
| **Sale** | Phones, electronics, goods | Buy | Commission on the price |
| **Rental** | Houses, cars | Rent / contact owner | Subscription |
| **Service** | Job applications on web, haircuts, cooking | Book / contact provider | Subscription |

Shared parts (title, images, seller, category, engagement counters) are common; only the type-specific parts differ. Build one product card and one product form with type-specific sections, not three copies.

### 3.2 Subscriptions and platform profit

The platform earns in two ways, and the admin controls both:

1. **Commission** — for sale products, the platform takes a percentage of the price (e.g. **12%** on a phone). The rate is a setting, not a hard-coded number.
2. **Subscription** — mainly for rental and service sellers, where there is no in-app sale price to take a cut from. The seller pays a plan to be reachable.

Rules:

- Subscription management is **fully dynamic**: the admin creates plans with any **amount** and any **duration** (and can edit or disable them).
- The admin can **require a subscription from any seller**, whatever they sell — including sale sellers — or exempt a seller.
- When a seller is required to subscribe and has **no active subscription**, their **contact info is hidden** from buyers. It is shown again once the subscription is paid.
- The hidden contact must be withheld **by the API**. The frontend shows a locked state when the field is absent; it must never receive the contact and hide it with CSS.

### 3.3 Referrals

- **Every user** has a personal referral link they can share outside the app.
- People who arrive through that link and register are linked to the referrer.
- When a referred person **buys or sells**, the referrer earns a **commission rate on that transaction**.
- Users see their link, the people they referred, and what they earned.

### 3.4 Wallets

- **Admin and sellers have wallets.**
- At this startup stage, balances are **numbers only (ledger money)**. Real money moves **outside the app**; the wallet records what is owed and what was settled.
- The UI must make this clear and must not look like a real payment/withdrawal product yet.

### 3.5 Social and engagement

Because the app connects many people around many kinds of products, engagement signals are a core feature, not decoration:

- **Wishlist** — save a product for later.
- **View count** — how many people viewed a listing.
- **Usage counters** — how many bought / rented / booked / contacted.
- Used to drive trust and discovery: "popular", "trending", "most viewed" sections and sorting.

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

- **Fonts:** *Plus Jakarta Sans* for headings (friendly, modern, strong at large sizes) and *Inter* for body and dashboard text (highly readable in dense tables and forms).
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

To be answered before the related feature is built:

1. **Referrer earnings** — only admin and sellers have wallets, but any user (including buyers) can earn referral commission. Where is a buyer's commission recorded — do all users get a wallet, or a separate "earnings" balance?
2. **Referral commission source** — is it taken from the platform's share, or added on top?
3. **Buying a sale product** — is there an in-app order/checkout flow, or does the buyer contact the seller and the seller records the sale?
4. **Backend** — base URL, authentication method (JWT / cookie), and the predefined permission list.
5. **Languages** — English only, or also Kinyarwanda / French?

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
- [x] Theme tokens in `src/index.css`: emerald primary, amber `highlight`, Inter + Plus Jakarta Sans, light and dark
- [x] Router with lazy routes, `PublicLayout` and `DashboardLayout`
- [x] API client (`lib/api.ts`) and TanStack Query provider
- [x] `useSession` hook with `can(permission)`; permission-driven sidebar and topbar
- [x] Dashboard shell: grouped sidebar with user menu, topbar with dark-mode toggle and notifications, per-page permission guard
- [x] Dashboard pages on demo data: Overview (stats, revenue chart), Products, Subscriptions (rates, plans, sellers), Referrals, Wallet, Users, Roles & permissions
- [x] Dashboard building blocks in `pages/dashboard/_components`: `DataTable`, `FormDialog`, `RowActions`, `StatCard`, `StatusBadge`, `PageHeader`
- [x] Marketplace header: search, wishlist count, type links, trust highlights, profile menu (email, referral link, theme, dashboard)
- [x] Footer with brand, the same links as the header, and social links
- [x] Home page: animated 3D hero, type banners, trending grid with tabs, highlights, referral banner
- [x] Products: browse page (search + type filter) and detail page with locked seller contact
- [x] Hero: location search (`/products?location=`), statistics that count up in three seconds
- [x] Cart (saved in the browser): buy button on every card and on the detail page, header cart icon, `/cart` page
- [x] Checkout (`/checkout`): receiver, delivery address (province, district, sector, cell) and the number the buyer pays from; confirmation with an order reference
- [x] Wishlist (saved in the browser), view and usage counters on cards
- [x] Animation system in `src/index.css`: `animate-float`, `animate-blob`, `animate-rise`, `reveal` (scroll), `stagger`

### Temporary — remove when the backend is connected
- `services/auth.ts` returns a demo admin while `VITE_API_URL` is not set.
- Permission names (`dashboard.view`, `product.manage`…) and the `/auth/me` endpoint are placeholders until the backend list is known.
- Dashboard pages keep their data in memory through `lib/demo-store.ts` (`_data.ts` files); changes are lost on reload. Replace each store with API queries and mutations.
- Dashboard listings are not linked to the storefront listings yet.
- `services/products.demo.ts` supplies demo listings (Unsplash photos) while `VITE_API_URL` is not set.
- The wishlist and the cart are stored in `localStorage` (`lib/id-store.ts`) until backend endpoints exist.
- `services/orders.ts` returns a demo reference and total while `VITE_API_URL` is not set: orders are not saved anywhere and `POST /orders` is a placeholder endpoint.
- Listing locations are demo towns; the location search matches the typed text, not real distance.
- Footer social links point to `#` until the real Muhuze accounts are known.
- The referral code (`DEMO2026`) comes from the demo user; the `/r/:code` landing route does not exist yet.
- Hero statistics (15K+ products…) and the floating chips are placeholder numbers.

### Next
- [ ] Auth pages (login, register) once the backend auth method is known
- [ ] Connect dashboard pages to the backend, one resource at a time
- [ ] Seller view of the dashboard (own listings, own wallet, own subscription)

### Later
- [ ] Order / contact flow for buying, renting and booking
- [ ] Referral registration through a shared link

### Change log
| Date | Change |
|---|---|
| 2026-10-01 | Project guide created; foundation and feature roadmap defined |
| 2026-10-01 | Foundation implemented: shadcn, theme, router, layouts, API client, session and permissions |
| 2026-10-01 | Buyer side redesigned: marketplace header, 3D animated hero, product browse, detail and wishlist |
| 2026-10-01 | Dashboard built: sidebar, topbar and seven working pages on demo data |
| 2026-10-05 | Header and footer reworked: highlights moved into the header, profile menu, social links; rule 20 added |
| 2026-10-05 | Hero location search and count-up statistics; cart with buy buttons, header icon and cart page |
| 2026-10-05 | Checkout with delivery details; payment happens outside the app |
