# 007 — Products

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §7](../../../README.md#7-products-categories-and-flexible-attributes). API contract: [`docs/api/products.md`](../api/products.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Let sellers list what they sell, and let buyers find it. This is the first feature buyers use without logging in, and what cart, orders, and payments will be built on.

## Scope

| In this feature | Not in this feature |
|---|---|
| Products: draft, publish, archive, delete a draft | Stock and "sold out" → `008_inventory` |
| Attribute values validated against the category | Variants (one product, several prices) → README §20 `K1` |
| Public product pictures | Filtering buyers' lists by attribute ("8 GB RAM") → [Known gaps](#known-gaps) |
| Buyer listing and product page, no login | Cart, orders, payment → later features |
| Seller's own list; staff moderation | Reviews, wishlist, view counts → README §20 `X6` |

## Lifecycle

```
          create
            │
            ▼
          DRAFT ──publish──► PUBLISHED ◄──publish── ARCHIVED
            │                    │                     ▲
          delete                 └──────archive────────┘
   (only if never published)
```

| Status | Buyers see it | Meaning |
|---|---|---|
| `draft` | No | Being prepared. May be incomplete. |
| `published` | Yes, if nothing behind it is switched off | On sale. |
| `archived` | No | Taken off sale by its seller. Can be published again. |

## Rules

**Decided 2026-10-07** (README §20 `K1`–`K4`, `T2`):

1. **No variants.** One product has one price. A phone in two storage sizes is two products.
2. **Attribute values are stored as checked rows**, each pointing at a real attribute and, for choices, a real option.
3. **No stock tracking.** A published product is simply available.
4. **No approval step.** A product is visible as soon as its seller publishes it; staff can hide one.
5. **One currency: RWF.**
6. **To publish**, a product needs an active category, a value for every required attribute, and at least one image.
7. **Up to 8 images**, JPEG or PNG, 5 MB each, stored publicly.
8. **Published products are archived, never deleted.** Only a draft that was never published can be deleted.

**Ownership**

- A product belongs to one seller and sits in one of **that seller's own** categories. Using another shop's category fails with "Category not found".
- Managing products needs, in order: the `product.manage` permission (sellers have it by default), an **active** seller, and ownership.
- Another shop's product behaves exactly like one that doesn't exist (`404`).

**Price**

- A decimal, never a float; more than 0; at most two decimal places. Returned as a string (`"850000.00"`).

**Attribute values**

- Sent as an object keyed by the attribute's `code`. The shape depends on the attribute's type:

  | Type | Value |
  |---|---|
  | `text` | a string, up to 500 characters |
  | `number` | a number (not `true`/`false`, not a string) |
  | `boolean` | `true` or `false` |
  | `select` | the **id** of one of the attribute's options |
  | `multi_select` | a list of option ids, at least one, no repeats |

- **All problems are reported at once**, named by attribute, and nothing is saved.
- In an update, only the codes that are sent are changed; `null` clears one.
- A switched-off attribute can no longer be set, but a value already stored is kept. A retired option stays on products that have it and cannot be chosen afresh.
- Moving a product to another category drops its attribute values: they belonged to the old category.
- A draft may be incomplete. Required attributes are enforced when publishing.

**Publishing**

- `publish_blockers` on the seller's view lists what is still missing; publishing works when it is empty.
- **A published product must stay complete.** An edit that would remove a required value, or deleting its last image, is refused as a whole.
- `published_at` is the first publication and never changes.

**What buyers see.** A product is visible only when **all** of these hold. Otherwise it is "not found", with no reason given:

- its status is `published`
- staff have not hidden it
- its category is active
- its shop is open (the seller is `active`)

The public list and the product page always agree.

**Staff moderation**

- Staff with `product.moderate` can see every product in any status and **hide** one. A hidden product disappears for buyers at once and **its seller cannot publish it**. Staff can **restore** it.

**Categories in use** (closes README §20 `K8`)

- A category that still has products cannot be deleted.
- An attribute, or an option, that products use cannot be deleted.
- Each can be switched off instead. The database's foreign keys enforce this, so the categories feature needs to know nothing about products.

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `product.manage` | Manage the products of your own shop | `seller` |
| `product.moderate` | See every product in any status; hide and restore | – |

## Design

```
app/modules/products/
├── product_routes.py        # /products (public), /products/mine, /products/moderation
├── product_dependencies.py
├── product_service.py       # every rule above; attribute validation; visibility
├── product_repository.py
├── product_model.py         # Product, ProductImage, ProductAttributeValue
├── product_schema.py
├── product_permissions.py
├── product_exceptions.py
└── product_constants.py
```

**How products use other features** (always through their services, AGENTS.md §7):

| Need | Call |
|---|---|
| The category and its attributes, to validate and display values | `CategoryService.get_own_category` / `get_category_definition` |
| "Is this shop open?" for one product page | `SellerService.get_open_shop` |
| Leaving out closed shops and inactive categories from a **list**, in SQL | `open_shop_ids()` and `visible_category_ids()`: subqueries those features provide, so the rule stays theirs and the list is still one query |

**Added for this feature**

- `FileStorage` gained **public images** (`upload_public_image`, `public_image_url`, `delete_public_image`), kept separate from private documents.
- `app/shared/slugs.py`: slug and code generation, shared with categories.

**Attribute value storage.** One table, `product_attribute_values`: one row per attribute for text, number, boolean, and select; one row per chosen option for multi-select. Exactly one of the four value columns is set (a database check), and a unique constraint with `NULLS NOT DISTINCT` allows only one row per attribute for the single-valued types. Requires PostgreSQL 15 or newer.

**Loading.** A list page costs two queries beyond the count: the products, and the main images of the whole page.

**Concurrency.** The product row is locked for every change to it, its images, or its values.

## Security review

- [x] Seller endpoints check permission, active seller, then ownership; a second shop was tested against all eight kinds of change.
- [x] A product can only be placed in the seller's own category.
- [x] Buyers can never reach a draft, archived, hidden, or closed-shop product, by list or by id, and are not told why.
- [x] Staff endpoints need `product.moderate`.
- [x] Attribute values are validated server-side against the category; unknown codes are rejected.
- [x] Images: type decided from content, size capped, count capped.
- [x] Price is a decimal end to end; a seller cannot set a negative or zero price.
- [x] Sort and filter values are an allowlist; search input is escaped.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| **No stock.** A seller can only stop selling by archiving | Overselling once orders exist | `008_inventory`, before orders |
| Buyers cannot filter a list by attribute value ("8 GB RAM", "Black") | Weaker browsing; the indexes for it exist | A follow-up to this feature |
| Search looks at the product name only | "Samsung" in the description is not found | Full-text search |
| No shop name on list items (only on the product page) | The frontend needs a second call to show it | Add when the frontend needs it |
| Images are not resized or checked for inappropriate content | Large or unsuitable pictures | Cloudinary transformations; moderation |
| No limit on how many products a seller creates | Abuse | Decide a limit, or rate-limit |
| No reason recorded when staff hide a product | The seller isn't told why | `014_notifications` |
| Renaming a product changes its public slug | Old links break | Keep old slugs as redirects |
| A product's price can change at any time | Fine today; orders must snapshot the price | `010_orders` (README §11.2) |

## Progress

- [x] Requirements and rules (this document, README §7, decisions `K1`–`K4`, `K8`, `T2`)
- [x] Database design and migration `0005` (applied to the development database)
- [x] Public image storage
- [x] Models, repository, service, schemas, routes, permissions
- [x] "In use" rules for categories, attributes, and options
- [x] Tests written: `tests/api/products/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [ ] **A real image upload to Cloudinary** (needs the `CLOUDINARY_*` values)
