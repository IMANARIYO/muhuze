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
- The UI therefore **checks permissions, never role names**. Write `can('<permission>')`, never `role === 'seller'`. A role created tomorrow must work without a code change. Permissions are named `<resource>.<action>` with a singular resource, e.g. `product.create` (README §5.4).
- Hiding a button is never security. The API enforces every permission, and the UI only reflects it.

### Layout per kind of user

| User | Layout |
|---|---|
| Buyer (no management permissions) | Public storefront layout: top navigation only. **Never a sidebar/dashboard.** |
| Admin, seller, and any role with management permissions | **One shared dashboard** with one sidebar and one topbar. Sidebar items, pages, and actions are shown or hidden by permission. |

There is exactly one dashboard and one sidebar in the codebase, not one per role.

### Permission codes

The codes are the backend's (`GET /authorization/me`), listed in each `backend/app/modules/*/*_permissions.py`. There is no "can open the dashboard" permission: holding any code in `lib/dashboard-access.ts` opens it, and each sidebar link names the codes that open its page (`permissions: ['product.manage', 'product.moderate']`). A seller's codes cover only their own shop (`product.manage`, `seller_order.manage`, `wallet.read_own`…); staff codes cover the platform (`payment.verify`, `product.moderate`, `revenue.read`…).

### Signing in

- The API client (`lib/api.ts`) keeps the access token in memory and the refresh token in `localStorage`, and refreshes on a `401`. **Only one refresh may run at a time** (a second use of an old refresh token signs the account out everywhere), so it is serialised within the tab and, through a Web Lock, across tabs.
- `useSession()` gives `user` (`null` for a visitor), `can(code)`, `reload()` after signing in, and `signOut()`.
- Pages that need an account sit under `layouts/RequireAuth.tsx`, which sends a visitor to `/login?next=…`.

### Becoming a seller (README §15, backend `docs/features/004_sellers.md`)

1. Any signed-in account applies once at `/sell`: shop name and phone, identity document type and number, location. The application starts as a **draft**.
2. They upload the identity document (front, and back unless it is a passport); business registration and TIN are optional. Files are private: the page asks for a five-minute link each time one is opened.
3. **Send for review** works once nothing required is missing. While it waits, nothing can be edited.
4. Staff approve or reject with a reason. A rejected application is edited and sent again; it is never deleted.
5. Approval makes the seller **active** and gives the account the `seller` role. Only an active seller may trade: the UI never treats the role as "can sell now", because a suspended or closed shop keeps the role.

### Products (README §7, backend `docs/features/007_products.md`)

- A listing belongs to one shop and sits in one of **that shop's own** categories; a category defines the details (attributes) its products carry.
- A new listing is a **draft**. To go on sale it needs an active category, every required detail, and at least one picture; the edit form shows what is still missing (`publish_blockers`).
- There is no approval step and no stock: a published listing is on sale at once, and its seller archives it when it is not available. Only a draft that was never published can be deleted.
- The dashboard's **Visible** switch keeps the original table design over the backend's statuses: for a seller it publishes or archives; for staff it restores or hides. A listing staff hid cannot be published by its seller.
- Buyers see a listing only when it is published, not hidden, in an active category, and its shop is open. Otherwise it is "not found".

### Order flow (README §8–§11)

0. Before anything can be ordered, staff must have set the default commission rate and at least one visible receiving account (dashboard Commission and Payment accounts; the dashboard warns while either is missing).
1. The cart lives on the device (README §20 `X8`). Checkout sends product ids and quantities with the delivery details; the backend reads every price and returns the order with its totals.
2. The order page shows MUHUZE's receiving accounts. Orders are **prepaid only**: mobile money, merchant code or bank transfer, never cash on delivery (README §20 `P8`). The buyer pays outside the app, then submits the transaction reference and the number they paid from.
3. Staff with `payment.verify` confirm or reject it on the dashboard's Payments page.
4. Only then does each shop see its part (dashboard Orders): accept or reject, ship, deliver. The buyer confirms receipt on the order page.

---

## 3. Features

The features and their rules are listed in the root README. Building a screen for a feature means following the README's confirmed rules for it.

Services and service providers are now confirmed in README §7.5 (request → accept → pay, phone number shown only while the provider has a subscription). Rentals are not. Some screens built before the backend existed showed ideas that are still **not confirmed** in the README (`X5`–`X7`, `V9`, `V12`): rentals, referrals, view and usage counters, location search. The storefront no longer shows them, because the backend has no data for them. The dashboard pages still marked as demo (section 9) do; change them to match whatever is decided when each is connected.

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

Business questions (referrer earnings, referral funding, buying flow, languages, authentication method, permission list) have moved to README §20 (`X1`–`X7`, `I3`, `F1`; authentication method and permission naming are already decided there), so every team works from one list. Add **frontend-only** questions here.

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
- [x] API client (`lib/api.ts`): unwraps the response envelope, throws `ApiError` with the backend's message, bearer token with single-flight refresh, `Page<T>`; TanStack Query provider
- [x] `useSession` hook on `GET /auth/me` + `GET /authorization/me`, with `can(permission)`; permission-driven sidebar and topbar
- [x] Auth pages: sign in, register, confirm email (six-digit code), forgot password, reset password (`/reset-password?token=`)
- [x] Dashboard shell: grouped sidebar with user menu, topbar with dark-mode toggle and notifications, per-page permission guard
- [x] Dashboard pages **still on demo data** (flagged `demo` in the sidebar, with a notice on the page): Overview, Referrals
- [x] Dashboard Payments (staff, `payment.verify`): confirm or reject reported payments. Dashboard Orders (seller, `seller_order.manage`): accept, reject, ship, deliver, with the delivery details and earnings of each order
- [x] Dashboard Orders, staff (`order.read`): every order from the moment it is placed, by status, with each shop's part and money split
- [x] Dashboard My wallet (seller, `wallet.read_own`): on the way, ready to withdraw, total earned, withdrawn, and every movement of the ledger
- [x] Dashboard Wallet (staff, `revenue.read`): commission income and totals, the revenue record of each sale, and any seller's balances (`wallet.read`)
- [x] Dashboard Roles & permissions (`role.read`; changes need `role.manage`): role cards with what each holds; create, rename, delete, and tick permissions from the backend's catalog. System roles keep their name, and the admin role always holds everything
- [x] Dashboard Users (`account.read`): every account with its roles; search by name or email and filter by role, both done by the backend; change an account's roles from the live list of roles (`role.assign`)
- [x] Dashboard Subscriptions (staff): plans (`seller_plan.manage`) — create, edit, offer or retire, delete; sellers' requests and subscriptions (`seller_subscription.manage`) — record payment to activate, decline, end
- [x] Dashboard My subscription (seller, `seller_subscription.request`): the commission paid now and why, plans on offer, request one, withdraw a pending request
- [x] Dashboard Payment accounts (staff, `payment_destination.manage`): MUHUZE's receiving accounts (add, edit, show or hide, default, delete)
- [x] Dashboard Commission (staff, `default_commission_rate.manage`): the default commission rate, with a note, and the history of every rate set
- [x] Dashboard setup warnings on every page, for staff who can fix them: commission rate not set, no visible payment account
- [x] Dashboard Products, seller (`product.manage`): own listings in any status, add and edit (category, price, description, the category's details, pictures), the **Visible** switch publishes or archives, delete a never-published draft
- [x] Dashboard Products, staff (`product.moderate`): every shop's listings; the **Visible** switch hides or restores one
- [x] Dashboard Categories (seller, `category.manage`): the shop's categories and the details (attributes) products in each carry
- [x] Storefront: a shop's listings can be narrowed to one of its categories
- [x] Become a seller (`/sell`, signed in): the application (shop, identity, location with optional GPS), private documents, send for review, and what each status means; close and reopen an approved shop
- [x] Dashboard Sellers (staff, `seller.read`): the review queue and every seller by status; open an application and its documents; approve or reject (`seller.review`), suspend or reinstate (`seller.suspend`)
- [x] Storefront shop listings: `/products?seller_id=`, linked from the seller card on a product page
- [x] Dashboard building blocks in `pages/dashboard/_components`: `DataTable`, `FormDialog`, `RowActions`, `StatCard`, `StatusBadge`, `PageHeader`
- [x] Marketplace header: search, wishlist and cart counts, sort links, trust highlights, Sign in button or profile menu (email, dashboard, my orders, theme, log out)
- [x] Footer with brand, the same links as the header, and social links
- [x] Home page on `GET /products`: animated 3D hero, newest products as tall picture cards and panels, lowest-priced products carousel
- [x] Products: browse page (search, shop filter, price sort, pages) and detail page (pictures, details, shop)
- [x] Hero: product search (`/products?q=`), statistics that count up in three seconds
- [x] Cart (saved in the browser, with quantities 1–999): button on the detail page, header cart icon, `/cart` page with an estimated total
- [x] Checkout (`/checkout`, signed in): delivery details, `POST /orders`
- [x] My orders (`/orders`) and the order page (`/orders/:id`): each shop's part and status, how to pay, report a payment, cancel while unpaid, confirm receipt
- [x] Route error screen (`pages/error.tsx`): reloads once when a page file is out of date, otherwise offers a reload
- [x] Wishlist (saved in the browser)
- [x] Referral page (`/referrals`, open to everyone), linked from the header bar: how the programme works; the user's link and results appear once the backend provides them
- [x] Animation system in `src/index.css`: `animate-float`, `animate-blob`, `animate-rise`, `reveal` (scroll), `stagger`

### Temporary
- `services/referrals.ts` answers `null` because the backend has no referral feature yet (README §20 `X5`), so `/referrals` shows "coming soon" to a signed-in user. Call the real endpoint there when it exists; the shared link is `/register?ref=<code>`, which the register page does not read yet.
- The dashboard pages flagged `demo` keep their data in memory through `lib/demo-store.ts` (`_data.ts` files, `services/products.demo.ts`, `services/orders.demo.ts`) and show one demo shop. Connect each to its backend API, then delete the demo files with the last of them.
- Dashboard tables load one page of 100 rows (the backend's maximum) and page through it in the browser. Move `DataTable` to server-side pages before a list can outgrow that.
- Development reaches the backend through the Vite proxy (`/api` → `http://localhost:8000`) because the backend sends no CORS headers. Production must serve both from one origin, or the backend must allow the frontend's origin.
- Footer social links point to `#` until the real Muhuze accounts are known.
- Hero statistics (15K+ products…) are placeholder numbers, not backend figures.

### Not in the backend yet (the storefront does not show these)
- A public list of shops, for a "Shops" menu: `GET /sellers` is staff-only.
- Filtering products by place: products carry no location.
- Product types, view and sold counters, referrals, server-side wishlist (README §20 `X1`–`X7`).
- Creating an account for someone else, and suspending or deleting one: the Users page has no Add, Suspend or Delete.
- Where a seller pays for a plan: MUHUZE's receiving accounts are shown only on a buyer's order, and a plan request carries no payment details. Staff activate it after checking the payment by hand.
- Error codes and per-field validation errors (README §20 `I3`): an unverified login is recognised by its message, and form errors are shown as one toast.

### Next
- [ ] Categories: rename an attribute, add or retire its options after creation; staff hide and restore (`category.moderate`)
- [ ] Withdrawals: a seller's payout accounts and requests, and staff review (`/withdrawals`, `/withdrawal/destinations`)
- [ ] Staff: a seller's status history; assign a plan to a seller directly; give a single permission directly to an account
- [ ] Account settings: change password, sessions

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
| 2026-10-10 | Backend connected: API client, authentication, storefront products, checkout, orders and payment reporting, staff payment confirmation, seller orders. Remaining dashboard pages flagged as demo |
| 2026-10-10 | Seller onboarding connected: `/sell` for the applicant, dashboard Sellers for staff review. Shared `FormField` and `RegionFields` |
| 2026-10-10 | Products connected: seller listings and categories, staff moderation, shop category filter on the storefront |
| 2026-10-10 | Cart quantities; staff Payment accounts page with the default commission rate |
| 2026-10-10 | Commission moved to its own page with history; setup warnings in the dashboard |
| 2026-10-10 | Staff view of all orders on the dashboard Orders page |
| 2026-10-10 | Wallets connected: the seller's wallet and ledger, staff revenue and seller balances |
| 2026-10-10 | Roles & permissions and subscriptions (plans, requests, the seller's side) connected |
| 2026-10-10 | Users page connected, on a new backend endpoint `GET /accounts` (see backend `docs/features/003_roles_and_permissions.md`) |
