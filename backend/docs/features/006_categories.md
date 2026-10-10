# 006 — Categories

**Status:** `TESTING`. Code, migration, tests, and docs are written, and the full flow was walked through against a real database. The test suite has not been run yet (see [Progress](#progress)).

Business rules: [`README.md` §7.2](../../../README.md#72-seller-owned-categories). API contract: [`docs/api/categories.md`](../api/categories.md). Tables: [`docs/database/database_schema.dbml`](../database/database_schema.dbml).

## Purpose

Let each seller organise their own shop into categories, and say what the products in each category are described by (Storage, Colour, Shoe size). Products (the next feature) are placed in a category and validated against its attributes.

## The model

**There is no shared marketplace tree.** Each seller creates and owns the categories of their own shop (decided 2026-10-06, `K7`).

```
Seller A's shop                         Seller B's shop
  ├── Phones                              ├── Smartphones
  │     ├── Storage  (number, GB)         │     └── Brand (text)
  │     └── Colour   (select)             └── Laptops
  │           Black · White · Blue
  └── Tablets
```

| Thing | What it is |
|---|---|
| **Category** | A section of one seller's shop. Flat: no parent, no subcategories. |
| **Attribute** | Something products in the category are described by. Has a type, and flags for "required" and "buyers can filter by it". |
| **Option** | One allowed value of a choice attribute. |

**What this gives up.** Buyers browse by category inside a shop and find products across shops by search. They cannot browse "all Phones" across the marketplace, because nothing ties one seller's category to another's. Adding marketplace-wide departments later is open (`K9`) and would not change these tables.

## Rules

**Who can do what**

- Managing categories needs three things, checked in this order: the `category.manage` permission (every seller has it by default), an **active** seller, and **ownership** of the category.
- A category of another shop behaves exactly like one that doesn't exist (`404`), for reading as well as changing.
- A suspended, deactivated, or not-yet-approved seller cannot manage categories.
- Buyers need no login to see a shop's categories.

**Categories**

- The name is unique within a shop, ignoring letter case. Two shops can both have "Phones".
- A web-friendly `slug` is made from the name (`Phones & Tablets` → `phones-tablets`) and is unique within the shop; a number is added on a clash (`t-shirts-2`). Renaming a category changes its slug.
- The seller chooses the display order (`sort_order`, lowest first; ties by name).
- A category can be switched off (`is_active: false`): hidden from buyers, kept by the seller.

**Attributes**

- Types: `text`, `number`, `boolean`, `select` (one option), `multi_select` (several options).
- **The type cannot be changed** after creation. To change it, add a new attribute and switch the old one off.
- Each attribute gets a stable `code` made from its first name (`Storage Size` → `storage_size`), unique within the category. **Renaming the attribute never changes its code**, so product data keyed by it stays valid.
- The name is unique within the category, ignoring letter case.
- A `unit` (GB, kg, cm) is only for `number` attributes.

**Options**

- Only `select` and `multi_select` attributes have options.
- Values are unique within the attribute, ignoring letter case.
- New options go to the end of the list unless a position is given.
- An option can be switched off (retired) instead of removed.

**What buyers see**

- Only active categories, with only their active attributes and active options.
- Only for a shop that is open: an unknown, unapproved, suspended, or closed shop returns `404`.

**Staff moderation**

- Staff with `category.moderate` can list every shop's categories and **hide** one that breaks the rules.
- A hidden category is off, and **its seller cannot switch it back on**. They can still see it and that it was hidden. Staff can **restore** it.

## Permissions

| Code | Allows | Default roles |
|---|---|---|
| `category.manage` | Manage the categories and attributes of your own shop | `seller` |
| `category.moderate` | See every shop's categories; hide and restore | – |

## Design

```
app/modules/categories/
├── category_routes.py        # /categories (seller + staff), /sellers/{id}/categories (public)
├── category_dependencies.py
├── category_service.py       # every rule above; slug and code generation
├── category_repository.py
├── category_model.py         # Category, CategoryAttribute, CategoryAttributeOption
├── category_schema.py
├── category_permissions.py
├── category_exceptions.py
└── category_constants.py
```

**Added to sellers for this feature**

- `SellerService.get_open_shop(seller_id)`: the seller if buyers may see the shop, otherwise `404`.
- `get_current_active_seller` (in `seller_dependencies.py`): the dependency any feature puts on an endpoint that only an active seller may use.

**Loading.** A category with its attributes and options is two queries beyond the category itself, whatever the number of categories on the page.

**Concurrency.** The category row is locked for every change to it or to its attributes and options.

## In use by products

Since the products feature (README §20 `K8`):

- A category that still has products cannot be deleted (`409`).
- An attribute, or an option, that products have values for cannot be deleted (`409`).
- Each can be switched off instead.

The database's `RESTRICT` foreign keys from the product tables are what say "in use"; `CategoryService` turns the refusal into a clear message and imports nothing from products.

## Security review

- [x] Every seller endpoint checks permission, active seller, then ownership; tested with a second shop against all nine kinds of change.
- [x] Another shop's category is indistinguishable from a missing one.
- [x] The public endpoint exposes only active data of open shops, and nothing about why a shop is closed.
- [x] Staff endpoints need `category.moderate`; a seller cannot hide or restore.
- [x] A staff hide cannot be undone by the seller.
- [x] Search input is escaped; no client value reaches `ORDER BY`.

## Known gaps

| Gap | Risk | Planned with |
|---|---|---|
| No limit on how many categories, attributes, or options a seller creates | A seller could create thousands | Decide a limit, or rate-limit |
| Sellers type any category names they like | Offensive or misleading names appear until staff hide them | Staff moderation exists; a report button would help |
| No reason is recorded when staff hide a category | The seller isn't told why | `014_notifications` / a reason field |
| Renaming a category changes its public slug | Old shop links to that category break | Keep old slugs as redirects, if links are shared |
| No cross-shop browsing by kind of product | Buyers rely on search | README §20 `K9` |

## Progress

- [x] Requirements and rules (this document, README §7.2, decision `K7`)
- [x] Database design and migration `0004` (applied to the development database)
- [x] Models, repository, service, schemas, routes, permissions
- [x] Tests written: `tests/api/categories/`
- [x] Full flow verified by hand against a real database (in a rolled-back transaction)
- [x] API and feature documentation
- [ ] **Tests run and passing** (run by the user: `cd backend && .venv/Scripts/python -m pytest -q`)
- [x] Deletion rules for categories, attributes, and options in use
