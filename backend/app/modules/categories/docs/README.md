# Categories Module

## Purpose

Manages the hierarchical product classification system for MUHUZE. Categories
answer: "What kind of thing is this product?" They drive navigation,
filtering, seller listing creation, attribute binding, and search.

## Responsibilities

- **Hierarchical classification** — self-referencing `parent_id` for unlimited nesting depth (Electronics > Phones > Smartphones).
- **Admin-controlled** — only admins create/rename/move/activate/deactivate categories. Sellers select from the existing catalog.
- **Attribute binding** — categories define which attributes apply, whether they are required, variant-defining, or filterable.
- **Display ordering** — `sort_order` controls the order categories appear in navigation.

## Does Not Handle

- **Product creation** — that's `products`. Categories classify products; they don't create them.
- **Attribute definitions** — that's `attributes`. Categories *bind* attributes; they don't define them.
- **Seller listing flow** — that's `seller_listings` (within `products`). Sellers select categories during listing creation.

## Architecture

Categories are a **self-referencing hierarchy** — one table, unlimited depth:

```
Electronics          (parent_id = NULL)
├── Phones           (parent_id = Electronics)
│   ├── Smartphones  (parent_id = Phones)
│   └── Feature Phones
├── Computers
│   ├── Laptops
│   └── Desktops
└── Cameras
    ├── Digital Cameras
    └── Camera Accessories
```

This avoids separate tables for `product_categories`, `product_subcategories`,
etc. — a single `categories` table with `parent_id` handles any depth.

**Admin-only management.** Sellers cannot create arbitrary categories. This
prevents catalog chaos ("Phones" vs "Mobile Phones" vs "Best Phones").
Sellers can *suggest* categories (future feature), but creation requires
admin review.

## Endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| GET | `/api/v1/categories` | No | List all categories (sorted by sort_order, then name) |
| GET | `/api/v1/categories/roots` | No | List top-level categories only |
| GET | `/api/v1/categories/{id}` | No | Get one category |
| GET | `/api/v1/categories/{id}/children` | No | List direct children of a category |
| POST | `/api/v1/categories` | Admin | Create a category |
| PATCH | `/api/v1/categories/{id}` | Admin | Update a category |

## Relationship to other modules

```
categories
    │
    │ 1:N
    ▼
products          (products belong to exactly one category)
    │
    │ 1:N
    ▼
product_variants  (variants are defined by category's variant attributes)

category_attributes
    │
    ├── categories  (which category)
    └── attributes  (which attribute applies)
```

## Module-owned docs

| Document | Purpose |
|---|---|
| [database.md](database.md) | Table schema reference |
| [hierarchy.md](hierarchy.md) | Self-referencing design, move validation, cycle prevention |
| [roadmap.md](roadmap.md) | What's done vs. planned |
