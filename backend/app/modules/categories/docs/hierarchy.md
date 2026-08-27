# Category Hierarchy

## Self-referencing design

Categories use a single table with a self-referencing `parent_id`:

```
┌───────────────┐
│  categories   │
│───────────────│
│ id            │
│ parent_id ────┼───┐  (FK → categories.id, nullable)
│ name          │   │
│ slug          │   │
│ ...           │   │
└───────────────┘   │
        ▲            │
        └────────────┘
```

This avoids separate tables for each nesting level. One table handles:

```
Electronics
├── Phones
│   ├── Smartphones
│   │   ├── Android
│   │   │   └── Samsung
│   │   └── iOS
│   └── Feature Phones
└── Computers
    ├── Laptops
    └── Desktops
```

## Traversal patterns

### Get all top-level categories

```sql
SELECT * FROM categories WHERE parent_id IS NULL ORDER BY sort_order, name;
```

### Get direct children of a category

```sql
SELECT * FROM categories WHERE parent_id = :parent_id ORDER BY sort_order, name;
```

### Get the full ancestor path (future)

```sql
WITH RECURSIVE ancestors AS (
    SELECT id, name, parent_id, 0 AS depth
    FROM categories WHERE id = :category_id
    UNION ALL
    SELECT c.id, c.name, c.parent_id, a.depth + 1
    FROM categories c JOIN ancestors a ON c.id = a.parent_id
)
SELECT * FROM ancestors ORDER BY depth DESC;
```

This powers breadcrumbs: Electronics > Phones > Smartphones.

## Cycle prevention

When moving a category, the system must prevent cycles:

```
BEFORE: Electronics → Phones → Smartphones
MOVE:   Electronics → Smartphones → Phones   ← CYCLE
```

The validation checks whether the target parent is a descendant of the
category being moved. If it is, the move is rejected.

**v1:** Move is not exposed via API. Categories are created in place.
Cycle prevention is documented for when move is implemented.

## Slug uniqueness

Slugs are globally unique across all categories, regardless of hierarchy.
This means `/smartphones` works as a URL without needing
`/electronics/phones/smartphones`.

The slug generation follows the same pattern as brands and products:
auto-generate from name, append `-2`, `-3` on collision.

## sort_order

`sort_order` controls display order within the same parent level:

```
Electronics (sort_order = 0)
├── Phones      (sort_order = 0)  ← shown first
├── Computers   (sort_order = 1)
└── Cameras     (sort_order = 2)
```

Categories are always displayed sorted by `sort_order` first, then `name`
as a tiebreaker. This lets admins control navigation without relying on
alphabetical order.
