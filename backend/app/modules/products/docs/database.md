# Products / Catalog Database

Conventions (UUID PK, timestamp mixin, table naming) are shared across all
modules — see [`auth/docs/database.md`](../../auth/docs/database.md#conventions-used-throughout).

## Overview

The catalog uses 9 tables organized in three layers:

1. **Attribute system** — `attributes`, `category_attributes` (what can vary)
2. **Product catalog** — `brands`, `products`, `product_variants`, `variant_attribute_values`, `product_images` (what exists)
3. **Seller bridge** — `seller_listings`, `listing_images` (who sells it and how)

See [erd.md](erd.md) for the visual relationship diagram.

**Implementation status:** all 9 tables exist in the schema (one
migration, so the shape is settled up front — see
[roadmap.md](roadmap.md)), but only `brands`, `attributes`, `products`,
`product_variants`, `variant_attribute_values`, and `product_images` have
a service/API layer built. `category_attributes` (enforcement of
required/variant/filterable per category) and `seller_listings` /
`listing_images` (the actual seller-offer flow) are schema-only for
now — deliberately deferred, not forgotten. Building the table now and
the logic later avoids a second migration touching foreign keys other
tables would already depend on.

---

## `brands`

Table: `brands` · Model: `app/modules/products/models.py::Brand`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| name | VARCHAR(150) | No | **Unique.** Display name (e.g., "Samsung", "Nike"). |
| slug | VARCHAR(170) | No | **Unique, indexed.** URL-safe identifier, auto-generated from name. |
| description | TEXT | Yes | Optional brand description or bio. |
| status | VARCHAR(20) | No | Indexed. One of `BrandStatus` — `active` or `inactive`. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Never hard-deleted.** Brands may be referenced by products with order
history. Lifecycle is status-only.

---

## `attributes`

Table: `attributes` · Model: `app/modules/products/models.py::Attribute`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| name | VARCHAR(100) | No | Display name (e.g., "Color", "Size", "RAM", "Storage"). |
| slug | VARCHAR(120) | No | **Unique, indexed.** URL-safe identifier. |
| input_type | VARCHAR(20) | No | How values are entered: `select` (dropdown), `text` (free-form), `number` (numeric with optional unit). |
| unit | VARCHAR(20) | Yes | Optional unit suffix (e.g., "GB", "mAh", "inches"). Display only — not used in queries. |
| status | VARCHAR(20) | No | Indexed. One of `AttributeStatus` — `active` or `inactive`. |
| created_at / updated_at | TIMESTAMPTZ | No | |

Attributes are admin-managed definitions. They define *what can vary* but
not the actual values — those live in `variant_attribute_values`.

**Examples:**

| name | slug | input_type | unit |
|---|---|---|---|
| Color | color | select | — |
| Size | size | select | — |
| RAM | ram | select | GB |
| Storage | storage | select | GB |
| Screen Size | screen-size | number | inches |
| Battery | battery | number | mAh |
| Material | material | select | — |
| Gender | gender | select | — |

---

## `category_attributes`

Table: `category_attributes` · Model: `app/modules/products/models.py::CategoryAttribute`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| category_id | UUID | No | FK → `categories.id`. Indexed. |
| attribute_id | UUID | No | FK → `attributes.id`. Indexed. |
| is_required | BOOLEAN | No | Whether products in this category *must* have this attribute. |
| is_variant | BOOLEAN | No | Whether this attribute *defines variants* (e.g., Color, Size). |
| is_filterable | BOOLEAN | No | Whether buyers can filter/search by this attribute. |
| sort_order | INTEGER | No | Display order within the category (lower = shown first). |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Unique on `(category_id, attribute_id)`** — an attribute can only be
bound to a category once.

**How the three flags work together:**

| is_required | is_variant | is_filterable | Meaning |
|---|---|---|---|
| True | True | True | Required + defines variants + filterable (e.g., Color for phones) |
| True | False | True | Required + not a variant + filterable (e.g., Brand for phones) |
| True | False | False | Required + not a variant + not filterable (e.g., Description) |
| False | True | True | Optional + defines variants + filterable (e.g., Color for shoes — optional if only one color) |
| False | False | True | Optional + not a variant + filterable (e.g., Material) |
| False | False | False | Optional + not a variant + not filterable (rare — used for metadata) |

**Variant generation:** When `is_variant = True`, the system uses this
attribute's values to generate product variants. For example, if a
category has two variant attributes (Color with 3 values, Size with 4
values), the product gets 3 × 4 = 12 variants.

See [attributes-and-variants.md](attributes-and-variants.md) for the full
attribute system design.

---

## `products`

Table: `products` · Model: `app/modules/products/models.py::Product`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| category_id | UUID | No | FK → `categories.id`. Indexed. A product belongs to exactly one category. |
| brand_id | UUID | Yes | FK → `brands.id`. Indexed. Nullable because not all products have a brand. |
| created_by_seller_id | UUID | Yes | FK → `sellers.id`. Indexed. Null means admin-curated directly; otherwise the seller who requested it — see [product-lifecycle.md](product-lifecycle.md#who-can-create-products). |
| name | VARCHAR(255) | No | Product name (e.g., "Samsung Galaxy A15"). |
| slug | VARCHAR(280) | No | **Unique, indexed.** URL-safe identifier, auto-generated from name. |
| description | TEXT | Yes | Product description. May contain markdown. |
| status | VARCHAR(20) | No | Indexed. One of `ProductStatus` — see [product-lifecycle.md](product-lifecycle.md). |
| rejection_reason | TEXT | Yes | Set on `reject()`, cleared on `submit_for_review()`/`approve()` — same pattern as `sellers.rejection_reason`. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**SPU (Standard Product Unit).** This is the canonical marketplace entry.
It does NOT contain price, stock, or seller information. Those live in
`seller_listings`.

A product's variants are defined by the category's variant attributes. The
product itself is the non-buyable grouping.

**Never hard-deleted.** Products with order history cannot be deleted
without destroying financial references.

---

## `product_variants`

Table: `product_variants` · Model: `app/modules/products/models.py::ProductVariant`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| product_id | UUID | No | FK → `products.id`, `ondelete="CASCADE"`. Indexed. |
| sku_code | VARCHAR(50) | Yes | Optional MUHUZE-internal SKU code. Auto-generated if not provided. |
| status | VARCHAR(20) | No | Indexed. One of `VariantStatus` — `active` or `inactive`. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**SKU (Stock Keeping Unit).** A specific version of a product, defined by
its combination of attribute values in `variant_attribute_values`.

**Variant identity:** A variant is uniquely identified by its combination
of attribute values within a product. Two variants of the same product
cannot have the same attribute value combination — enforced at the
application level when creating variants.

**Multiple sellers can offer the same variant** at different prices and
stock levels through `seller_listings`.

---

## `variant_attribute_values`

Table: `variant_attribute_values` · Model: `app/modules/products/models.py::VariantAttributeValue`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| variant_id | UUID | No | FK → `product_variants.id`, `ondelete="CASCADE"`. Indexed. |
| attribute_id | UUID | No | FK → `attributes.id`. Indexed. |
| value | VARCHAR(255) | No | The actual value (e.g., "Black", "256GB", "8GB"). |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Unique on `(variant_id, attribute_id)`** — a variant can only have one
value per attribute.

**Examples:**

| variant | attribute | value |
|---|---|---|
| Samsung A15 / 256GB / Black | Color | Black |
| Samsung A15 / 256GB / Black | Storage | 256GB |
| Nike AF1 / White / 42 | Color | White |
| Nike AF1 / White / 42 | Size | 42 |

This table is the bridge between the abstract attribute definitions and
the concrete variant values. It enables:

- Filtering: "Show me all variants where Color = Black"
- Display: "This variant comes in Black, 256GB"
- Uniqueness: prevent duplicate variants within a product

---

## `product_images`

Table: `product_images` · Model: `app/modules/products/models.py::ProductImage`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| product_id | UUID | No | FK → `products.id`, `ondelete="CASCADE"`. Indexed. |
| cloudinary_public_id | VARCHAR(255) | No | Cloudinary's identifier — needed to delete or re-sign access. |
| cloudinary_resource_type | VARCHAR(20) | No | Cloudinary's `resource_type` (`image`, `video`). |
| original_filename | VARCHAR(255) | Yes | As uploaded — display only, never trusted for content-type. |
| mime_type | VARCHAR(100) | No | |
| file_size | INTEGER | No | Bytes. |
| sort_order | INTEGER | No | Display order (lower = shown first). |
| is_primary | BOOLEAN | No | Whether this is the main product image. At most one per product. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Canonical product images** — stock photos, brand images, manufacturer
photos. These represent the product itself, not a specific seller's
actual stock.

Uploaded with `delivery_type="upload"` (public), **not** the
`"authenticated"` pattern `seller_documents` uses — a buyer browsing the
catalog needs a fast, CDN-cacheable, publicly reachable image, not a
freshly-signed URL on every request. `url` is built locally and
deterministically from `cloudinary_public_id` via
`storage.get_public_url()` (no signing, no network call). See
[`core/docs/storage.md`](../../../core/docs/storage.md).

---

## `seller_listings`

Table: `seller_listings` · Model: `app/modules/products/models.py::SellerListing`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| seller_id | UUID | No | FK → `sellers.id`. Indexed. |
| variant_id | UUID | No | FK → `product_variants.id`. Indexed. |
| price | NUMERIC(12,2) | No | Price in RWF. Must be > 0. |
| stock | INTEGER | No | Available quantity. Must be >= 0. |
| seller_sku | VARCHAR(100) | Yes | The seller's own SKU code for this variant. |
| condition | VARCHAR(20) | No | One of `ListingCondition` — `new`, `used`, `refurbished`. |
| status | VARCHAR(20) | No | Indexed. One of `ListingStatus` — see below. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Unique on `(seller_id, variant_id)`** — a seller can only have one
listing per variant. This is the marketplace rule: same seller, same
variant, one offer.

**This is the bridge between the catalog and the seller.** It answers:
"How is this seller selling this variant?" The variant knows what the
product is. The listing knows the price, stock, and seller.

**Listing statuses:**

| Status | Meaning |
|---|---|
| `draft` | Listing created, not yet submitted. Editable. |
| `pending_review` | Submitted, awaiting admin approval. Not editable. |
| `active` | Approved. Visible to buyers. |
| `rejected` | Admin rejected. Editable again for resubmission. |
| `suspended` | Was active, admin temporarily removed from visibility. |
| `out_of_stock` | Was active, stock reached 0. Automatically set. |
| `archived` | Seller or admin archived. Not visible to buyers. |

See [seller-listing-flow.md](seller-listing-flow.md) for the full
listing lifecycle.

**Financial connection:**

```
seller_listings → order_items → payments → revenue_transactions → wallets
```

When a buyer purchases from a listing, the order records the listing_id,
seller_id, variant_id, price, and quantity. This feeds into the financial
architecture defined in the project README.

---

## `listing_images`

Table: `listing_images` · Model: `app/modules/products/models.py::ListingImage`

| Column | Type | Nullable | Description |
|---|---|---|---|
| id | UUID | No | Primary key |
| listing_id | UUID | No | FK → `seller_listings.id`, `ondelete="CASCADE"`. Indexed. |
| cloudinary_public_id | VARCHAR(255) | No | Cloudinary's identifier. |
| cloudinary_resource_type | VARCHAR(20) | No | Cloudinary's `resource_type`. |
| original_filename | VARCHAR(255) | Yes | As uploaded — display only. |
| mime_type | VARCHAR(100) | No | |
| file_size | INTEGER | No | Bytes. |
| sort_order | INTEGER | No | Display order. |
| is_primary | BOOLEAN | No | Whether this is the main listing image. At most one per listing. |
| created_at / updated_at | TIMESTAMPTZ | No | |

**Seller-specific product photos.** These show the seller's actual stock,
not the canonical product image. A buyer sees listing images when viewing
a specific seller's offer.

---

## Why these 9 tables and not more

| Concern | Where it lives | Why not a separate table |
|---|---|---|
| Brand | `brands` | Already a table — brands are reusable across products |
| Attribute definitions | `attributes` | Already a table — attributes are reusable across categories |
| Attribute-category binding | `category_attributes` | Junction table with flags — needed for the attribute system |
| Product definition | `products` | The SPU — core catalog entry |
| Variant definition | `product_variants` | The SKU — buyable unit |
| Variant attribute values | `variant_attribute_values` | Key-value store per variant — enables filtering and uniqueness |
| Product images | `product_images` | Canonical images for the product |
| Seller offers | `seller_listings` | Bridge between catalog and sellers — price, stock, seller SKU |
| Listing images | `listing_images` | Seller-specific photos |

**What we're deliberately NOT building yet:**

| Concern | Why not now |
|---|---|
| `inventory` table | Stock is a column on `seller_listings` for v1. Advanced inventory (reservations, backorders, warehouses) is a future concern. |
| `product_reviews` | Planned for later. Not part of the catalog core. |
| `product_questions` | Planned for later. |
| `product_moderation` | Admin review via listing status transitions. No separate moderation queue yet. |
| `product_matching` | Admin dedup via review. No automated matching yet. |
| `search_index` | PostgreSQL full-text search for v1. Dedicated search engine (Elasticsearch/Meilisearch) is a future upgrade. |
