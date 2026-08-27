# Seller Listing Flow

## Prerequisites

Before a seller can create a listing, two conditions must be met:

1. **Seller must be `active`** — `Seller.status == "active"` (approved by
   admin). Checked at the service layer, not just via `require_role("seller")`.
2. **Product must be `active`** — the product must exist in the marketplace
   catalog with `Product.status == "active"`.

## The complete flow

```
                         ACCOUNT
                            │
                            ▼
                          SELLER
                            │
                    Seller Active?
                            │
                         YES
                            │
                            ▼
                    CREATE LISTING
                            │
                            ▼
                  SELECT CATEGORY
                            │
                            ▼
                LOAD CATEGORY ATTRIBUTES
                            │
                            │  ┌─── required attributes
                            │  ├─── optional attributes
                            │  └─── variant attributes
                            ▼
                  SEARCH CATALOG
                     /          \
                    /            \
                 FOUND          NOT FOUND
                   │                │
                   ▼                ▼
             SELECT PRODUCT    REQUEST PRODUCT
                   │                │
                   │           ADMIN REVIEW
                   │                │
                   │          ┌─────┴─────┐
                   │          │           │
                   │       APPROVED     REJECTED
                   │          │
                   └──────┬───┘
                          ▼
                    SELECT VARIANTS
                          │
                          ▼
                  ENTER SELLER DATA
                          │
                 ┌────────┼─────────┐
                 ▼        ▼         ▼
               PRICE     STOCK     SKU
                 │        │         │
                 └────────┼─────────┘
                          ▼
                    UPLOAD IMAGES
                          │
                          ▼
                  SUBMIT LISTING
                          │
                          ▼
                    ADMIN REVIEW
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                APPROVED      REJECTED
                    │
                    ▼
                  ACTIVE
                    │
                    ▼
              BUYERS CAN FIND IT
```

## Step by step

### 1. Seller selects a category

The seller picks a category (e.g., "Electronics > Phones > Smartphones").
This determines which attributes are available.

### 2. System loads category rules

The system queries `category_attributes` for the selected category:

- **Required attributes:** Brand, Product Name (must be filled)
- **Optional attributes:** Material, Gender (may be filled)
- **Variant attributes:** Color, Storage, RAM (define which variants exist)

### 3. Seller searches the catalog

The seller searches for the product they want to sell:

```
Seller types: "Samsung Galaxy A15"
System searches: products.name LIKE '%Samsung Galaxy A15%'
Results: Samsung Galaxy A15, Samsung Galaxy A25, Samsung Galaxy A16
```

### 4a. Product found

The seller selects the existing product. No new product is created.

### 4b. Product not found

The seller requests a new product. The system creates a product with
`status = pending_review`. Admin reviews before it enters the catalog.

### 5. Seller selects variants

The system shows the available variants for the selected product:

```
Samsung Galaxy A15
├── 128GB / 4GB / Black
├── 128GB / 4GB / Blue
├── 256GB / 8GB / Black
└── 256GB / 8GB / Blue
```

The seller selects which variants they want to list.

### 6. Seller enters their data

For each selected variant, the seller provides:

| Field | Required | Description |
|---|---|---|
| `price` | Yes | Price in RWF. Must be > 0. |
| `stock` | Yes | Available quantity. Must be >= 0. |
| `seller_sku` | No | The seller's own SKU code for this variant. |
| `condition` | Yes | `new`, `used`, or `refurbished`. |

### 7. Seller uploads images

Seller uploads their own product photos (actual stock photos). These go to
`listing_images`, not `product_images`.

### 8. Seller submits

Listing status changes to `pending_review`.

### 9. Admin reviews

Admin checks:

- Is the price reasonable?
- Is the stock accurate?
- Are the images appropriate?
- Is the condition accurate?
- Does the listing match the correct variant?

### 10. Admin approves or rejects

**Approve:** Status → `active`. Visible to buyers.

**Reject:** Status → `rejected`. Seller can edit and resubmit.

## Listing status transitions

```
                     create()
                         │
                         ▼
                      DRAFT ───────────────┐
                         │                 │
              submit_for_review()          │ update()
                         │                 │ (edit while draft/rejected)
                         ▼                 │
                PENDING_REVIEW             │
                    │        │             │
               approve()  reject()         │
                    │        │             │
                    ▼        ▼             │
                ACTIVE   REJECTED ─────────┘
                  │  ▲
         suspend()│  │reactivate()
                  ▼  │
              SUSPENDED
                  │
          out_of_stock()
                  │
                  ▼
            OUT_OF_STOCK
                  │
              restock()
                  │
                  ▼
                ACTIVE

ACTIVE ──archive()──► ARCHIVED
```

## Editability

| Status | Can Edit? | Can Upload Images? |
|---|---|---|
| `draft` | Yes | Yes |
| `pending_review` | No | No |
| `active` | No (price/stock changes via separate endpoints) | No |
| `rejected` | Yes | Yes |
| `suspended` | No | No |
| `out_of_stock` | No (restock only) | No |
| `archived` | No | No |

**Active listing modifications:** Price and stock can be updated via
dedicated endpoints (`PATCH /listings/{id}/price`,
`PATCH /listings/{id}/stock`) without going through the full review cycle.
Other fields (description, images) require resubmission.

## Out of stock handling

When `stock` reaches 0, the listing automatically transitions to
`out_of_stock`. When the seller restocks (sets stock > 0), it transitions
back to `active` without going through admin review.

## Duplicate prevention

The unique constraint `(seller_id, variant_id)` prevents a seller from
creating multiple listings for the same variant. If Seller A already has
an active listing for "Samsung A15 / 256GB / Black", they cannot create
another one — they must update the existing listing.

## Buyer visibility

A listing is visible to buyers only when:

1. `seller_listings.status = "active"`
2. `product_variants.status = "active"`
3. `products.status = "active"`
4. `sellers.status = "active"`

All four must be true. If any is false, the listing is suppressed from
search results and product pages.
