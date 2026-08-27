# Products / Catalog Module

## Purpose

Manages the MUHUZE product catalog: the canonical definitions of products,
their variants, attribute system, brand registry, and the bridge between
the catalog and sellers through listings. This module answers three
questions:

1. **What exists in the marketplace?** — Products, variants, brands, categories, attributes.
2. **How is it organized?** — Category-driven attributes, SPU/SKU hierarchy, variant generation.
3. **Who is selling it and how?** — Seller listings with price, stock, seller SKU, and condition.

## Responsibilities

- **Brands** — brand registry (name, slug, status). Admin-managed.
- **Attributes** — attribute definitions (Color, Size, RAM, etc.) with input types and units.
- **Category-attribute binding** — which attributes apply to which category, whether they are required, variant-defining, or filterable.
- **Products (SPU)** — canonical product entries belonging to a category and brand. The non-buyable grouping.
- **Product variants (SKU)** — specific combinations of attribute values under a product (e.g., "256GB / Black"). Each variant is buyable.
- **Variant attribute values** — the actual attribute values that define each variant.
- **Product images** — canonical product images (stock/brand photos).
- **Seller listings** — a seller's offer for a specific variant: price, stock, seller SKU, condition.
- **Listing images** — seller-specific product photos (actual stock photos).

## Does Not Handle

- **Order placement** — that's `orders`. A listing is what gets ordered; the order itself is a different domain.
- **Payment processing** — that's `payments`.
- **Search indexing** — a future `search` module will consume catalog data for full-text and faceted search.
- **Product reviews/ratings** — planned for later, not part of the catalog core.
- **Inventory management** — stock is a column on `seller_listings` for v1. Advanced inventory (reservations, backorders, warehouse tracking) is a future concern.
- **Category CRUD** — that's the `categories` module (already implemented, not yet mounted).

## Architecture

The catalog follows a three-level hierarchy inspired by Alibaba's seller tooling:

```
CATALOG
   │
   ▼
PRODUCT (SPU)        ← "What is this product?"
   │
   ▼
VARIANT (SKU)        ← "Which specific version?"
   │
   ▼
SELLER LISTING       ← "Who sells it, at what price?"
```

The key architectural rule:

> **Creating a catalog Product is not the same thing as a Seller creating a Listing.**

A Product is a canonical marketplace entry. A Listing is a seller's offer
for a specific variant of that product. Multiple sellers can list the same
variant at different prices and stock levels.

Each endpoint flows through 4 layers:

```
router.py       → route declarations only (path, method, request/response schema)
controller.py    → HTTP layer: translates schemas ⇄ service calls
service.py       → business rules (validation, slug generation, status transitions)
repository.py    → data access only (SQLAlchemy queries), no business rules
```

### Module-owned docs

| Document | Purpose |
|---|---|
| [catalog-design.md](catalog-design.md) | The SPU → SKU → Listing architecture and why it matters |
| [erd.md](erd.md) | Visual entity-relationship diagram for all catalog tables |
| [database.md](database.md) | Full table-by-table schema reference |
| [attributes-and-variants.md](attributes-and-variants.md) | How the attribute system drives variant generation |
| [product-lifecycle.md](product-lifecycle.md) | Product status transitions and rules |
| [creation-scenarios.md](creation-scenarios.md) | Admin-creates vs. seller-requests a product, side by side, with real request/response examples |
| [seller-listing-flow.md](seller-listing-flow.md) | How a seller creates and manages listings |
| [roadmap.md](roadmap.md) | Implementation phases checklist |

## Tables

| Table | Purpose |
|---|---|
| `brands` | Brand registry (Samsung, Nike, etc.) |
| `attributes` | Attribute definitions (Color, Size, RAM, etc.) |
| `category_attributes` | Which attributes apply to which category |
| `products` | Canonical product entries (SPU) |
| `product_variants` | Specific variants under a product (SKU) |
| `variant_attribute_values` | Attribute values defining each variant |
| `product_images` | Canonical product images |
| `seller_listings` | Seller offers for specific variants |
| `listing_images` | Seller-specific product photos |

## Relationship to other modules

```
categories (existing) ─────┐
                            ▼
                   ┌─────────────────┐
                   │   PRODUCTS /    │
                   │    CATALOG      │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          sellers       orders        search
         (existing)    (future)      (future)
```

- **categories** — products belong to categories; categories define which attributes apply.
- **sellers** — sellers create listings for catalog variants. Seller must be `active` to list.
- **orders** — orders reference seller listings. Each order item knows exactly which variant from which seller.
- **search** — will consume catalog data for full-text search and faceted filtering.
