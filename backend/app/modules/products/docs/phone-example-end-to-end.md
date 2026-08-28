# Marketplace Example — end to end (Phone, Computer, Food) from catalog to commission

Three concrete, fully worked examples so everyone on the team — product, design,
frontend, backend — sees exactly **who creates what**, **what the customer sees**,
and **what the seller earns**. This is not an architectural document (see
`catalog-design.md`, `seller-listing-flow.md`, `attributes-and-variants.md`,
`product-lifecycle.md`); it is a walk-through of real listings, from the admin
setting up the catalog, to sellers listing their products, to a customer browsing
the storefront, to the money splitting after each sale.

All of the flows below are **live and tested**. The exact endpoint sequence is
codified in `backend/tests/test_catalog.py` (`publish_product_with_listing`) and
`backend/tests/test_commerce.py` (the buy / pay / receive path with the 12% / 7%
commission and the escrow).

Every request below is real — the same calls the tests make against `/api/v1`.

---

## The three products in this example

| # | Product | Category | Sellers | Variants |
|---|---|---|---|---|
| 1 | **Samsung Galaxy A15** (phone) | Phones | TechnoPlus Kigali | 128GB/Black, 256GB/Blue-Black |
| 2 | **Dell XPS 13** (computer / laptop) | Computers | Urban Tech Hub | 16GB/512GB, 32GB/1TB |
| 3 | **Long Grain Rice 5kg** (food) | Food & Groceries | Farm Fresh Kigali **and** Market Plus | Single variant, two sellers (competing offers) |

The phone is the deepest example. The computer shows "different category, same
pattern". The food shows the most important marketplace behavior: **two sellers
offering the same variant at different prices**, and how the customer chooses.

---

## Part 0 — Who creates what (roles)

The marketplace has a strict division of labour. In one line:

> **The admin curates the shared catalog vocabulary. Sellers author products,
> variants and their own offers. Customers only browse and buy.**

### The three roles

- **Admin** — owns the *shared vocabulary* that everything else hangs off:
  categories, brands, attributes, and the filter settings for each category.
  Approves products and listings before they go live.
- **Seller** — an approved (active) seller creates *offers*: a product request,
  variants, and listings with their own price/stock. Sellers never create the
  vocabulary — they pick from it.
- **Customer** — browses the public catalog and product pages, buys, pays by
  Airtel Money, confirms receipt.

### Admin-only vs. seller actions (endpoints)

| Thing | Endpoint | Who can do it | Why it's restricted |
|---|---|---|---|
| **Category** | `POST /api/v1/categories` | **Admin only** | Sellers pick from an existing tree so the catalog doesn't fragment ("Phones" vs "Phone" vs "Mobile Phones") |
| **Brand** | `POST /api/v1/brands` | **Admin only** | Controlled vocabulary so "Samsung" / "samsung" / "Samsung Inc" don't become three rows |
| **Attribute** | `POST /api/v1/attributes` | **Admin only** | A global vocabulary sellers draw from when defining variants — no free-text invention |
| **Category-attribute binding / filters** | (admin/seed config) | **Admin only** | Decides which attributes are required/variant/filterable per category |
| **Product (SPU)** | `POST /api/v1/products` | **Admin** (curates directly) **or active seller** (requests one) | Sellers can *request* a new product; it goes through approval |
| **Variant (SKU)** | `POST /api/v1/products/{id}/variants` | **Admin or active seller** | Active sellers can add variants once the product is active (shared catalog) |
| **Product image** | `POST /api/v1/products/{id}/images` | **Admin or active seller** | Canonical images visible to buyers |
| **Listing (offer)** | `POST /api/v1/listings` | **Seller** (their own offer) | Price/stock/condition are the seller's business |
| **Listing approval** | `POST /api/v1/listings/{id}/approve` | **Admin only** | Admin reviews before it's buyable |
| **Browse storefront** | `GET /api/v1/catalog*` | **Anyone (public, no auth)** | Customers (and not-yet-logged-in visitors) browse freely |

**And what the seller cannot touch:** categories, brands, and attributes. When a
seller wants to sell something in a category that doesn't exist yet, they request
it from admin (or admin creates it). The seller's tooling only lets them *select*
from the curated lists.

> Let's make that concrete with two roles:
> - **TechnoPlus Kigali** cannot create a "Phones" category — the admin did.
> - **The admin** does not set TechnoPlus's price on the Galaxy A15 — TechnoPlus does.

---

## Part 1 — Admin sets up the catalog vocabulary

These steps are done **once by an admin**, not per sale. Each product's category,
brand and attributes:

### 1.1 Categories

```
POST /api/v1/categories            (admin token)
{ "name": "Phones", "description": "Mobile phones and smartphones" }

POST /api/v1/categories            (admin token)
{ "name": "Computers", "description": "Laptops, desktops and accessories" }

POST /api/v1/categories            (admin token)
{ "name": "Food & Groceries", "description": "Fresh and packaged food" }
```

### 1.2 Brands

```
POST /api/v1/brands                (admin token)
{ "name": "Samsung" }

POST /api/v1/brands                (admin token)
{ "name": "Dell" }
```

(A "brand" for food is optional — the rice just won't have a `brand_id`.)

### 1.3 Attributes

Attributes are global and admin-curated; sellers reuse them when defining variants.

```
# Phones & computers share some attributes:
POST /api/v1/attributes            (admin token)
{ "name": "Storage", "input_type": "select", "unit": "GB" }

POST /api/v1/attributes            (admin token)
{ "name": "RAM", "input_type": "select", "unit": "GB" }

POST /api/v1/attributes            (admin token)
{ "name": "Color", "input_type": "select" }

# Food uses its own:
POST /api/v1/attributes            (admin token)
{ "name": "Packaging", "input_type": "select" }
```

> **Filters:** which attributes appear as storefront checkboxes per category, and
> whether they are required / variant-defining / filterable, is the
> `category_attributes` junction set by admin/seed. If `Storage.is_filterable`
> is set for Phones, the shopper gets a "Storage" filter group with live values.

---

## Part 2 — The sellers get approved to sell

A normal user registers and becomes a seller; the admin must approve them before
anything they list is visible or buyable.

```
POST /api/v1/auth/register
{ "email": "technoplus@example.com", "password": "supersecret123" }

POST /api/v1/auth/login
{ "email": "technoplus@example.com", "password": "supersecret123" }
# -> returns { access_token, refresh_token }; use the access_token as a Bearer.

POST /api/v1/sellers               (technoplus token)
{ "business_name": "TechnoPlus Kigali" }

POST /api/v1/sellers/me/documents  (technoplus token, multipart)
data:  { "document_type": "national_id_front" }
file:  <national_id_front.jpg>

POST /api/v1/sellers/me/submit     (technoplus token)

POST /api/v1/sellers/{seller_id}/approve   (admin token)
# -> seller status: "active"
```

The phone's seller (TechnoPlus) and the computer's seller (Urban Tech Hub)
and the food sellers (Farm Fresh Kigali, Market Plus) all go through this same
approval. Each seller can double-check their status and their **live commission
rate**:

```
GET /api/v1/premium/me             (technoplus token)
# -> { "seller_id": ..., "is_premium": false, "commission_rate": 12.0, ... }
```

---

## Part 3 — Each seller creates products and variants

### 3.1 The phone — Samsung Galaxy A15 (TechnoPlus Kigali)

Sellers never invent a category/brand — they select the IDs the admin created.

```
POST /api/v1/products              (technoplus token)
{
  "category_id": "<phones-id>",
  "brand_id":    "<samsung-id>",
  "name":        "Samsung Galaxy A15",
  "description": "6.5\" display, 5000 mAh battery, dual SIM"
}
# -> ProductResponse, status: "draft"
```

First image is automatically primary (public Cloudinary URL, buyers see it):

```
POST /api/v1/products/{product_id}/images   (technoplus token, multipart)
data:  { "is_primary": "true" }
file:  <galaxy-a15.jpg>
```

Two variants — each a distinct combination of attribute values:

```
POST /api/v1/products/{product_id}/variants   (technoplus token)
{ "sku_code": "SAM-A15-128-BLK",
  "attribute_values": [
    { "attribute_id": "<storage-id>", "value": "128GB" },
    { "attribute_id": "<color-id>",   "value": "Black" } ] }

POST /api/v1/products/{product_id}/variants   (technoplus token)
{ "sku_code": "SAM-A15-256-BLKBLU",
  "attribute_values": [
    { "attribute_id": "<storage-id>", "value": "256GB" },
    { "attribute_id": "<color-id>",   "value": "Blue-Black" } ] }
```

Submit + admin approve:

```
POST /api/v1/products/{product_id}/submit    (technoplus token)   # draft -> pending_review
POST /api/v1/products/{product_id}/approve   (admin token)        # -> active
```

### 3.2 The computer — Dell XPS 13 (Urban Tech Hub)

Same pattern, different category and attributes (Storage **and** RAM define the
variants).

```
POST /api/v1/products              (urban-tech token)
{
  "category_id": "<computers-id>",
  "brand_id":    "<dell-id>",
  "name":        "Dell XPS 13",
  "description": "13.3\" InfinityEdge, Core i7, silver aluminum"
}
# status: "draft"

POST /api/v1/products/{product_id}/images   (urban-tech token, multipart)  -> primary image

POST /api/v1/products/{product_id}/variants   (urban-tech token)
{ "sku_code": "XPS-16-512",
  "attribute_values": [
    { "attribute_id": "<ram-id>",      "value": "16GB"  },
    { "attribute_id": "<storage-id>",  "value": "512GB" } ] }

POST /api/v1/products/{product_id}/variants   (urban-tech token)
{ "sku_code": "XPS-32-1T",
  "attribute_values": [
    { "attribute_id": "<ram-id>",      "value": "32GB" },
    { "attribute_id": "<storage-id>",  "value": "1TB"  } ] }

POST /api/v1/products/{product_id}/submit    (urban-tech token)
POST /api/v1/products/{product_id}/approve   (admin token)
```

### 3.3 The food — Long Grain Rice 5kg (Farm Fresh Kigali)

Food is simpler: one variant. It also shows that a brand is **optional**.

```
POST /api/v1/products              (farm-fresh token)
{
  "category_id": "<food-id>",
  "name":        "Long Grain Rice 5kg",
  "description": "Premium long grain rice, 5kg bag"
}
# status: "draft"

POST /api/v1/products/{product_id}/images   (farm-fresh token, multipart)  -> primary image

POST /api/v1/products/{product_id}/variants   (farm-fresh token)
{ "sku_code": "RICE-5KG",
  "attribute_values": [
    { "attribute_id": "<packaging-id>", "value": "5kg bag" } ] }

POST /api/v1/products/{product_id}/submit    (farm-fresh token)
POST /api/v1/products/{product_id}/approve   (admin token)
```

---

## Part 4 — Sellers list variants for sale

A **listing** is a seller's *offer* — their price, stock, condition and SKU for a
specific variant.

### 4.1 Phone — two listings (TechnoPlus)

```
POST /api/v1/listings              (technoplus token)
{ "variant_id": "<a15-128gb>", "price": 300000, "stock": 10,
  "seller_sku": "TP-128-BLK",   "condition": "new" }

POST /api/v1/listings              (technoplus token)
{ "variant_id": "<a15-256gb>", "price": 350000, "stock": 10,
  "seller_sku": "TP-256-BLKBLU", "condition": "new" }
```

### 4.2 Computer — two listings (Urban Tech Hub)

```
POST /api/v1/listings              (urban-tech token)
{ "variant_id": "<xps-16-512>", "price": 1400000, "stock": 5, "condition": "new" }

POST /api/v1/listings              (urban-tech token)
{ "variant_id": "<xps-32-1t>",  "price": 1700000, "stock": 3, "condition": "new" }
```

### 4.3 Food — the SAME variant, TWO sellers

This is the key marketplace moment. Both sellers list the **same** rice variant
at different prices. Each seller can only have **one** listing per variant.

```
# Farm Fresh Kigali
POST /api/v1/listings              (farm-fresh token)
{ "variant_id": "<rice-5kg>", "price": 12000, "stock": 100, "condition": "new" }

# Market Plus — same variant, different price
POST /api/v1/listings              (market-plus token)
{ "variant_id": "<rice-5kg>", "price": 12500, "stock": 60,  "condition": "new" }
```

Every listing must be submitted + approved before it's buyable:

```
POST /api/v1/listings/{listing_id}/submit    (seller token)   # draft -> pending_review
POST /api/v1/listings/{listing_id}/approve   (admin token)    # -> active
```

> A listing is visible to buyers only when `seller.status`, `product.status`,
> `variant.status`, **and** `listing.status` are all `active` (see
> `seller-listing-flow.md`). Draft, rejected, suspended, or archived listings are
> never shown.

---

## Part 5 — What the customer sees

The customer is **not** talking to the database model. They see products, variants
and sellers. Nothing here needs auth — the catalog endpoints are public.

### 5.1 The storefront grid / search

```
GET /api/v1/catalog
```

Returns every active offer as a card-ready row. It would contain the three products:

```jsonc
[
  {
    "listing_id": "<tp-128gb>", "price": 300000.0, "stock": 10, "condition": "new",
    "product": { "id": "<a15>", "name": "Samsung Galaxy A15",
        "slug": "samsung-galaxy-a15", "description": "6.5\" display...", "category_id": "<phones-id>" },
    "variant": { "id": "<a15-128gb>", "sku_code": "SAM-A15-128-BLK",
        "attribute_values": [
          { "attribute_id": "<storage>", "attribute_name": "Storage", "value": "128GB" },
          { "attribute_id": "<color>",   "attribute_name": "Color",   "value": "Black" } ] },
    "seller": { "id": "<technoplus>", "business_name": "TechnoPlus Kigali" },
    "images": [{ "id": "<img>", "url": "https://res.cloudinary.com/.../galaxy-a15.jpg",
                "is_primary": true, "sort_order": 0 }]
  },
  {
    "listing_id": "<xps-16-512>", "price": 1400000.0, "stock": 5, "condition": "new",
    "product": { "id": "<xps>", "name": "Dell XPS 13",
        "slug": "dell-xps-13", "description": "13.3\" InfinityEdge...", "category_id": "<computers-id>" },
    "variant": { "id": "<xps-16-512>", "sku_code": "XPS-16-512",
        "attribute_values": [
          { "attribute_id": "<ram>",     "attribute_name": "RAM",     "value": "16GB" },
          { "attribute_id": "<storage>", "attribute_name": "Storage", "value": "512GB" } ] },
    "seller": { "id": "<urban-tech>", "business_name": "Urban Tech Hub" },
    "images": [{ "id": "<img>", "url": "https://res.cloudinary.com/.../xps-13.jpg",
                "is_primary": true, "sort_order": 0 }]
  },
  // the rice appears TWICE — once per seller offer on the same product/variant:
  {
    "listing_id": "<farm-fresh-rice>", "price": 12000.0, "stock": 100, "condition": "new",
    "product": { "id": "<rice>", "name": "Long Grain Rice 5kg", "slug": "long-grain-rice-5kg",
        "description": "Premium long grain rice, 5kg bag", "category_id": "<food-id>" },
    "variant": { "id": "<rice-5kg>", "sku_code": "RICE-5KG",
        "attribute_values": [
          { "attribute_id": "<packaging>", "attribute_name": "Packaging", "value": "5kg bag" } ] },
    "seller": { "id": "<farm-fresh>", "business_name": "Farm Fresh Kigali" },
    "images": [{ "id": "<img>", "url": "https://res.cloudinary.com/.../rice.jpg",
                "is_primary": true, "sort_order": 0 }]
  },
  {
    "listing_id": "<market-plus-rice>", "price": 12500.0, "stock": 60, "condition": "new",
    "product": { "id": "<rice>", "name": "Long Grain Rice 5kg", "slug": "long-grain-rice-5kg",
        "description": "Premium long grain rice, 5kg bag", "category_id": "<food-id>" },
    "variant": { "id": "<rice-5kg>", "sku_code": "RICE-5KG",
        "attribute_values": [
          { "attribute_id": "<packaging>", "attribute_name": "Packaging", "value": "5kg bag" } ] },
    "seller": { "id": "<market-plus>", "business_name": "Market Plus" },
    "images": [{ "id": "<img>", "url": "https://res.cloudinary.com/.../rice.jpg",
                "is_primary": true, "sort_order": 0 }]
  }
]
```

Notice: the rice is **one product, one variant** — but two rows, one per seller.
That's the whole point of the SPU → SKU → Listing model (`catalog-design.md`).

**Filters a shopper can use** (all optional, combinatorics allowed):

```
# The filter sidebar is data-driven — the frontend just renders it:
GET /api/v1/catalog/filters?category_id=<phones-id>
# -> { category_ids, brands: [...],
#      attributes: [{ name: "Storage", values: ["128GB","256GB"] }, ...],
#      price_range: { min, max }, conditions: ["new"] }

GET /api/v1/catalog?search=dell
GET /api/v1/catalog?search=rice
GET /api/v1/catalog?category_id=<food-id>
GET /api/v1/catalog?in_stock=true
GET /api/v1/catalog?min_price=10000&max_price=13000
GET /api/v1/catalog?attribute_id=<storage>&value=256GB
GET /api/v1/catalog?sort=price_desc
```

### 5.2 The product detail page (variants + who's selling)

Because `product ≠ seller`, the same endpoint renders any product. For the **rice**
it's the clearest: one variant, **two offers**, and the customer picks a seller.

```
GET /api/v1/catalog/products/<rice-id>
```

```jsonc
{
  "id": "<rice-id>",
  "name": "Long Grain Rice 5kg",
  "slug": "long-grain-rice-5kg",
  "description": "Premium long grain rice, 5kg bag",
  "category_id": "<food-id>",
  "brand_id": null,
  "images": [{ "id": "<img>", "url": "https://res.cloudinary.com/.../rice.jpg", "is_primary": true, "sort_order": 0 }],
  "variants": [
    {
      "id": "<rice-5kg>",
      "sku_code": "RICE-5KG",
      "attribute_values": [
        { "attribute_id": "<packaging>", "attribute_name": "Packaging", "value": "5kg bag" } ],
      "offers": [
        { "listing_id": "<farm-fresh-rice>", "price": 12000.0, "stock": 100,
          "condition": "new", "seller": { "id": "<farm-fresh>",  "business_name": "Farm Fresh Kigali" } },
        { "listing_id": "<market-plus-rice>", "price": 12500.0, "stock": 60,
          "condition": "new", "seller": { "id": "<market-plus>", "business_name": "Market Plus" } }
      ]
    }
  ]
}
```

The **Samsung Galaxy A15** detail looks the same shape but with two variants, each
with the single TechnoPlus offer — exactly as in the previous version of this doc.
**Dell XPS 13** likewise shows its two variants (16GB/512GB and 32GB/1TB).

**What the customer never sees:** the seller's internal SKU, the listing status,
and the backend's tidy separation of `product ≠ variant ≠ listing`. They just see
"Long Grain Rice 5kg — 12,000 RWF from Farm Fresh, or 12,500 RWF from Market Plus."

---

## Part 6 — A customer buys, pays, and the money splits

Using the rice as the example. Add a saved address (optional but common):

```
POST /api/v1/addresses             (customer token)
{ "recipient_name": "Alice M.", "phone": "+250788000001",
  "street": "KN 4 Ave", "city": "Kigali", "country": "RW" }

POST /api/v1/carts/items           (customer token)
{ "listing_id": "<farm-fresh-rice>", "quantity": 1 }
```

Checkout (creates the order + a revenue line for **each** seller in the order):

```
POST /api/v1/orders                (customer token)
{ "shipping": { "recipient_name": "Alice M.", "phone": "+250788000001",
                "city": "Kigali", "country": "RW" } }
```

Pay by Airtel Money (a real PSP can replace the stub gateway):

```
POST /api/v1/payments              (customer token)
{ "order_id": "<order-id>",
  "momo_phone": "+250788000001",      # mobile-money number
  "airtel_phone": "+250722000002" }   # Airtel Money number

POST /api/v1/payments/{payment_id}/paid   (customer token)   # marks paid (idempotent)
```

### 6.1 The commission / escrow math

The **basic** seller pays **12%**, a **premium** seller pays the plan's rate
(default **7%**). The rate is snapshotted onto the revenue line at sale time and
comes from `GET /api/v1/premium/me`.

Worked numbers:

| Product | Gross | Seller | Rate | MUHUZE cut (`commission_amount`) | Seller earning (`held`→`released`) |
|---|---|---|---|---|---|
| Galaxy A15 128GB | 300,000 | TechnoPlus (basic) | 12% | 36,000 | 264,000 |
| Galaxy A15 256GB | 350,000 | TechnoPlus (basic) | 12% | 42,000 | 308,000 |
| Dell XPS 13 16GB | 1,400,000 | Urban Tech (basic) | 12% | 168,000 | 1,232,000 |
| Rice 5kg | 12,000 | Farm Fresh (basic) | 12% | 1,440 | 10,560 |
| Rice 5kg | 12,500 | Market Plus (premium) | 7% | 875 | 11,625 |

**Escrow rule (see `backend/docs/financial-flow-design.md`):**
- On **payment success** (`paid`), MUHUZE keeps `commission_amount` immediately;
  the seller's `seller_earning` is marked `held`.
- The held earning is **only released** once the **customer confirms receipt** of
  the order — and only once (release is idempotent).

Inspect the breakdown (admin):

```
GET /api/v1/revenue/order/<order-id>   (admin token)
# -> [{ seller_id: "<farm-fresh>", amount: 12000, revenue_rate: 12.0,
#       commission_amount: 1440, seller_earning: 10560,
#       status: "held", released_at: null },
#      ... one entry per seller in the order ]
```

If the customer bought both sellers' items in one order (e.g. rice from Farm Fresh
**and** a power bank from another seller), the order gets **one revenue line per
seller**, each with its own rate and escrow.

### 6.2 Fulfillment → receipt → release (the full loop)

```
POST /api/v1/orders/seller/<seller-order-id>/accept          (seller token)
POST /api/v1/orders/seller/<seller-order-id>/ship            (seller token)
  { "carrier": "DHL", "tracking_number": "TRK-9" }
POST /api/v1/orders/seller/shipments/<shipment-id>/deliver   (seller token)

# customer confirms they received it:
POST /api/v1/orders/<order-id>/receive                       (customer token)
# -> order completed_at set; each seller's revenue line flips held -> released once
```

The customer tracks each seller's slice through `GET /api/v1/orders/<order-id>`:
the `fulfillment[]` array shows `pending → accepted → shipped` (with tracking) →
`delivered`, then their `receive` completes the order and releases the money.

---

## Quick reference — the exact endpoints used

| Step | Method & path | Who |
|---|---|---|
| category / brand / attribute | `POST /api/v1/categories`, `POST /api/v1/brands`, `POST /api/v1/attributes` | **admin** |
| become approved seller | `POST /auth/register` · `/login` · `/sellers` · `/sellers/me/documents` · `/sellers/me/submit`, then `/sellers/{id}/approve` | seller + admin |
| check own commission | `GET /api/v1/premium/me` | seller |
| create product + image + variants | `POST /api/v1/products`, `POST /products/{id}/images`, `POST /products/{id}/variants` | seller |
| approve product | `POST /products/{id}/submit` → `POST /products/{id}/approve` | seller → admin |
| list for sale | `POST /api/v1/listings` → `/listings/{id}/submit` → `/listings/{id}/approve` | seller → admin |
| **browse the storefront** | `GET /api/v1/catalog`, `GET /api/v1/catalog/products/{id}`, `GET /api/v1/catalog/filters` | **public (customer)** |
| buy + pay | `POST /api/v1/orders`, `POST /api/v1/payments`, `POST /payments/{id}/paid` | customer |
| fulfill | `POST /api/v1/orders/seller/{id}/accept|ship`, `.../shipments/{id}/deliver` | seller |
| confirm receipt | `POST /api/v1/orders/{id}/receive` | customer |
| see the split | `GET /api/v1/revenue/order/{id}` | admin |
