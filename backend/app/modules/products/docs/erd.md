# Entity Relationship Diagram

## Full catalog ERD

```
┌─────────────────────┐       ┌──────────────────────┐
│     categories      │       │       brands         │
│─────────────────────│       │──────────────────────│
│ id            (PK)  │       │ id             (PK)  │
│ parent_id     (FK)  │──┐    │ name           (UQ)  │
│ name               │  │    │ slug           (UQ)  │
│ slug          (UQ)  │  │    │ description         │
│ description        │  │    │ status               │
│ status             │  │    │ created_at           │
│ created_at         │  │    │ updated_at           │
│ updated_at         │  │    └──────────┬───────────┘
└─────────┬───────────┘  │             │
          │              │             │
          │ self-ref     │             │
          └──────────────┘             │
                                       │
          ┌────────────────────────────┤
          │                            │
          ▼                            │
┌─────────────────────────┐            │
│       products          │            │
│─────────────────────────│            │
│ id                (PK)  │            │
│ category_id       (FK)  │────────────┘
│ brand_id          (FK)  │─────────────── (nullable)
│ name                   │
│ slug              (UQ)  │
│ description            │
│ status                 │
│ created_at             │
│ updated_at             │
└─────────┬───────────────┘
          │
          │ 1
          │
          │ N
┌─────────┴───────────────┐        ┌──────────────────────────┐
│   product_variants      │        │       attributes         │
│─────────────────────────│        │──────────────────────────│
│ id                (PK)  │        │ id                 (PK)  │
│ product_id        (FK)  │        │ name                     │
│ sku_code              │        │ slug              (UQ)    │
│ status                 │        │ input_type               │
│ created_at             │        │ unit                (N)  │
│ updated_at             │        │ status                   │
└─────────┬───────────────┘        │ created_at               │
          │                        │ updated_at               │
          │ 1                      └──────────┬───────────────┘
          │                                   │
          │ N                                 │
┌─────────┴────────────────────┐              │
│  variant_attribute_values    │              │
│──────────────────────────────│              │
│ id                     (PK)  │              │
│ variant_id             (FK)  │              │
│ attribute_id           (FK)  │──────────────┘
│ value                       │
│ created_at                  │
│ updated_at                  │
│                              │
│ UQ(variant_id, attribute_id) │
└──────────────────────────────┘


┌─────────────────────────┐
│   category_attributes   │
│─────────────────────────│
│ id                (PK)  │
│ category_id       (FK)  │──→ categories.id
│ attribute_id      (FK)  │──→ attributes.id
│ is_required            │
│ is_variant             │
│ is_filterable          │
│ sort_order             │
│ created_at             │
│ updated_at             │
│                         │
│ UQ(category_id, attr_id)│
└─────────────────────────┘


┌─────────────────────────┐        ┌──────────────────────────┐
│    product_images       │        │    seller_listings       │
│─────────────────────────│        │──────────────────────────│
│ id                (PK)  │        │ id                 (PK)  │
│ product_id        (FK)  │        │ seller_id          (FK)  │──→ sellers.id
│ cloudinary_public_id   │        │ variant_id         (FK)  │──→ product_variants.id
│ cloudinary_resource_type│       │ price                     │
│ original_filename (N)  │        │ stock                     │
│ mime_type              │        │ seller_sku                │
│ file_size              │        │ condition                 │
│ sort_order             │        │ status                    │
│ is_primary             │        │ created_at                │
│ created_at             │        │ updated_at                │
│ updated_at             │        │                            │
│                         │        │ UQ(seller_id, variant_id) │
└─────────────────────────┘        └──────────┬───────────────┘
                                              │
                                              │ 1
                                              │
                                              │ N
                                     ┌────────┴────────────┐
                                     │   listing_images    │
                                     │─────────────────────│
                                     │ id            (PK)  │
                                     │ listing_id    (FK)  │
                                     │ cloudinary_public_id│
                                     │ cloudinary_resource_type│
                                     │ original_filename(N)│
                                     │ mime_type           │
                                     │ file_size           │
                                     │ sort_order          │
                                     │ is_primary          │
                                     │ created_at          │
                                     │ updated_at          │
                                     └─────────────────────┘
```

## Cross-module relationships

```
accounts (1) ──── (0..1) sellers
sellers  (1) ──── (0..N) seller_listings
seller_listings (1) ──── (0..N) listing_images

categories (1) ──── (0..N) products
brands     (1) ──── (0..N) products
products   (1) ──── (1..N) product_variants
product_variants (1) ──── (0..N) variant_attribute_values
attributes (1) ──── (0..N) variant_attribute_values
categories (1) ──── (0..N) category_attributes
attributes (1) ──── (0..N) category_attributes
products   (1) ──── (0..N) product_images

sellers    (1) ──── (0..N) seller_listings
product_variants (1) ──── (0..N) seller_listings
```

## Future extensions (not yet built)

```
seller_listings (1) ──── (0..N) order_items
seller_listings (1) ──── (0..1) inventory        (advanced stock management)
products       (1) ──── (0..N) product_reviews
products       (1) ──── (0..N) product_questions
```
