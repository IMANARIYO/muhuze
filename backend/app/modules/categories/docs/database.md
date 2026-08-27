# Categories Database

Conventions (UUID PK, timestamp mixin, table naming) are shared across all
modules — see [`auth/docs/database.md`](../../auth/docs/database.md#conventions-used-throughout).

## `categories`

Table: `categories` · Model: `app/modules/categories/models.py::Category`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| parent_id | UUID | Yes | FK → `categories.id` (self-referential). Indexed. NULL for top-level categories. |
| name | VARCHAR(150) | No | Display name (e.g., "Smartphones"). |
| slug | VARCHAR(170) | No | **Unique, indexed.** URL-safe identifier, auto-generated from name. |
| description | TEXT | Yes | Optional category description. |
| image | VARCHAR(255) | Yes | Cloudinary public ID for category image/icon. |
| sort_order | INTEGER | No | Display order within parent (lower = shown first). Default 0. |
| status | VARCHAR(20) | No | Indexed. One of `CategoryStatus` — `active` or `inactive`. |
| created_at / updated_at | TIMESTAMPTZ | No | |

## Self-referencing hierarchy

```
categories (1) ──── (0..N) categories   (via parent_id)
```

A category's `parent_id` points to another row in the same table. NULL
means top-level. This gives unlimited nesting depth without multiple
tables.

**Example:**

| id | parent_id | name | slug | sort_order |
|---|---|---|---|---|
| (uuid) | NULL | Electronics | electronics | 0 |
| (uuid) | Electronics.id | Phones | phones | 0 |
| (uuid) | Phones.id | Smartphones | smartphones | 0 |
| (uuid) | Electronics.id | Computers | computers | 1 |

## Ordering

Categories are ordered by `sort_order` first, then `name` as a tiebreaker.
This allows admins to control display order: "Phones" before "Computers"
regardless of alphabetical order.

## Status lifecycle

```
ACTIVE ──deactivate()──► INACTIVE
INACTIVE ──activate()──► ACTIVE
```

Soft-deactivation only. Never hard-deleted — products with order history
may reference the category.

## Relationship to products

```
categories (1) ──── (0..N) products
```

A product belongs to exactly one category. The category determines which
attributes apply (via `category_attributes`), which drives variant
generation and buyer filtering.

## Relationship to attributes

```
categories (1) ──── (0..N) category_attributes
attributes (1) ──── (0..N) category_attributes
```

The `category_attributes` junction table (in the `products` module) binds
attributes to categories with flags: `is_required`, `is_variant`,
`is_filterable`. See
[`products/docs/attributes-and-variants.md`](../../products/docs/attributes-and-variants.md).
