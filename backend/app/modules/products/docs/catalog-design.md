# Catalog Design

## The core insight

Most beginner marketplace designs make one fatal mistake: they treat
"product" as a single flat row containing everything — name, price, stock,
images, seller info. This breaks immediately when:

- Multiple sellers sell the same product at different prices.
- A product has variants (sizes, colors, storage options).
- You need to search/filter by brand, category, or attributes.
- A seller's stock is separate from the product definition.

MUHUZE avoids this by separating three distinct concepts:

> **Product ≠ SKU ≠ Seller's offer**

## The three levels

```
                    PRODUCT / SPU
                         │
              "Samsung Galaxy A15"
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
       SKU 1           SKU 2           SKU 3
      128GB            256GB            256GB
      Black            Black            Blue
          │              │              │
          └──────────────┼──────────────┘
                         │
                    SELLER OFFER
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Seller A   Seller B   Seller C
           $300       $315       $295
```

### Level 1: Product (SPU — Standard Product Unit)

The canonical, non-buyable product definition. Answers: **"What is this
product?"**

```
Product: Samsung Galaxy A15
Category: Electronics > Phones > Smartphones
Brand: Samsung
Description: 6.5" display, 5000mAh battery...
```

A product does NOT contain price, stock, or seller information. It is a
marketplace-level entity, not a seller-level entity.

**Multiple sellers sell the same product.** The product is the shared
catalog entry they all reference.

### Level 2: Variant (SKU — Stock Keeping Unit)

A specific version of a product, defined by its attribute values. Answers:
**"Which specific version of this product?"**

```
Variant: Samsung Galaxy A15 / 256GB / Black
Variant: Samsung Galaxy A15 / 256GB / Blue
Variant: Samsung Galaxy A15 / 128GB / Black
```

Variants are generated from the category's variant attributes. If the
category says "phones vary by Color and Storage", then every combination
of Color × Storage is a distinct variant.

Each variant can have its own inventory, and multiple sellers can offer
the same variant.

### Level 3: Seller Listing

A seller's offer for a specific variant. Answers: **"How is this seller
selling this variant?"**

```
Seller: ABC Electronics
Variant: Samsung Galaxy A15 / 256GB / Black
Price: 350,000 RWF
Stock: 10
Seller SKU: SAM-A15-256-BLK
Condition: New
```

```
Seller: XYZ Electronics
Variant: Samsung Galaxy A15 / 256GB / Black
Price: 340,000 RWF
Stock: 5
Seller SKU: XYZ-A15-BLK-256
Condition: New
```

Same variant, different sellers, different prices and stock. This is the
marketplace experience.

## Why this matters

### Multiple sellers become trivial

When Seller B wants to sell "Nike Air Force 1 / White / 42":

1. They search the catalog → find "Nike Air Force 1".
2. They select the variant "White / 42".
3. They create a listing with their price and stock.

They do NOT create another "Nike Air Force 1" product. They create
another **listing** for the existing variant.

```
Product: Nike Air Force 1
   │
   └── Variant: White / 42
          │
          ├── Seller A → 82,000 RWF → stock 7
          ├── Seller B → 79,000 RWF → stock 3
          └── Seller C → 85,000 RWF → stock 12
```

Buyers see all three offers and choose.

### Search and filtering become clean

Because attributes are structured (not free-text), we can:

- Filter by brand: "Show me Samsung products"
- Filter by attribute: "Show me phones with 256GB storage"
- Filter by price: "Show me offers under 350,000 RWF"
- Faceted search: "Show me the available colors for this product"

### Orders know exactly what was purchased

When a customer buys, the order records:

```
OrderItem
  ├── product_id    → Samsung Galaxy A15
  ├── variant_id    → 256GB / Black
  ├── listing_id    → ABC Electronics' listing
  ├── seller_id     → ABC Electronics
  ├── quantity      → 1
  ├── unit_price    → 350,000 RWF
  └── total         → 350,000 RWF
```

This feeds directly into the financial architecture:

```
OrderItem → Payment → RevenueTransaction → Seller Earning → Wallet → Withdrawal
```

### The catalog stays clean

Without this separation, you get:

```
Product #1: "Samsung Galaxy A15 256GB Black"  (created by Seller A)
Product #2: "Samsung A15 256GB Black"          (created by Seller B)
Product #3: "Galaxy A15 Black 256GB"           (created by Seller C)
```

Three "different" products that are actually the same thing. With the
SPU/SKU/Listing model, there is exactly one product, one variant, and
three listings.

## The seller's perspective vs. the buyer's perspective

These are two different views over the same data.

### Seller sees

```
My Listings

Nike Air Force 1
├── White / 40 → 80,000 RWF → 5 available
├── White / 41 → 80,000 RWF → 10 available
├── White / 42 → 82,000 RWF → 7 available
└── White / 43 → 82,000 RWF → 3 available
```

### Buyer sees

```
Nike Air Force 1

Available from 12 sellers
From 80,000 RWF

Sizes: 40  41  42  43
Colors: White  Black
```

The buyer does not need to understand the database structure. They see a
product, pick a variant, and choose a seller.

## The seller SKU concept

Alibaba uses "SellerSku" — an identifier from the seller's own operational
perspective. MUHUZE should allow this.

Different sellers may use different naming conventions for the same variant:

| Seller | Seller SKU | MUHUZE Variant |
|---|---|---|
| ABC Electronics | SAM-A15-256-BLK | Samsung A15 / 256GB / Black |
| XYZ Electronics | A15-BLACK-256 | Samsung A15 / 256GB / Black |
| Phone World | PHONE-001 | Samsung A15 / 256GB / Black |

All three `seller_sku` values point to the same canonical variant. This
helps sellers with their own inventory management while keeping the
marketplace catalog clean.

## What Alibaba got right that we're borrowing

1. **SPU + SKU separation** — product grouping vs. buyable variant.
2. **Seller listing is separate from product** — "a seller creates an offer,
   not a product."
3. **Category-driven attributes** — attributes are defined per category,
   not invented by sellers.
4. **Seller SKU** — seller's own operational identifier alongside the
   canonical variant.
5. **Search by attributes** — structured attributes enable faceted search.

## What we're NOT copying from Alibaba

1. **Complexity** — Alibaba has 30+ tables for catalog. We start with 9.
2. **B2B features** — MOQ, trade assurance, supplier tiers. Not MUHUZE v1.
3. **Product matching/merging** — Alibaba has sophisticated dedup. We use
   admin review instead.
4. **Search infrastructure** — Alibaba uses Elasticsearch. We'll start with
   PostgreSQL full-text search and upgrade later.

## The most important rule

> **Don't think: "A seller uploads a product."**
>
> **Think: "A seller creates an offer for a product in the marketplace catalog."**

That small change in thinking prevents most of the architectural problems
that plague marketplace platforms.
