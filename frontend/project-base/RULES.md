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
