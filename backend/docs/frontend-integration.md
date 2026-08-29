# Frontend Integration Guide — MUHUZE Global Link API

This guide tells the frontend team exactly what to call to let a buyer
**browse the catalog** and **add items to the cart**, from login through
checkout hand-off. It is written for the `v1` API only.

Base URL (dev): `http://127.0.0.1:8000`
API root: `/api/v1` → so every endpoint below is `/api/v1/...`
Interactive docs (Swagger UI): `http://127.0.0.1:8000/docs`

---

## 1. The response envelope

**Every** endpoint returns the same shape. Do not expect a raw array or
object — always read `data`:

```json
{
  "status": "success",
  "message": "Some human-readable message",
  "data": { }
}
```

- `status`: `"success"` or `"error"`.
- On errors, `data` is `null`. Error responses also use this envelope;
  check `status === "error"` and show `message` to the user.
- HTTP status codes still apply on top of the envelope (200/201 for
  success, 400/401/403/404/422 for the common failures).

Your API client should unwrap `data` once and ignore the envelope for the
rest of the flow.

---

## 2. Authentication (needed for cart, NOT for browsing)

Catalog browsing is **public** (no token required). Adding to cart and
checkout **require** that the buyer is logged in.

### Register — `POST /api/v1/auth/register`

```json
{
  "email": "buyer@example.com",
  "password": "at-least-8-chars",
  "phone": null
}
```

`phone` is optional. Returns an account object. The account starts
**unverified** (email verification is a separate step; see `/api/v1/auth/email/verification/request` + `/confirm`).

### Login — `POST /api/v1/auth/login`

```json
{
  "email": "buyer@example.com",
  "password": "at-least-8-chars"
}
```

Returns a token pair:

```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "<jwt>",
    "refresh_token": "<jwt>",
    "token_type": "bearer"
  }
}
```

### Using the access token

Every **authenticated** request (anything under Cart, plus buyer identity)
must send:

```
Authorization: Bearer <access_token>
```

The access token is short-lived. When it expires (HTTP `401`), exchange it
for a fresh pair via `POST /api/v1/auth/refresh` with body
`{"refresh_token": "<refresh_token>"}` — then retry the original call.
Store both tokens securely (e.g. httpOnly cookie or an in-memory store +
secure storage for refresh).

> Note: your `token_type` is `bearer`, so the header value is
> `Bearer <access_token>` — do not re-prefix with "JWT ".

---

## 3. Browse the catalog (public, no auth)

### List what's for sale — `GET /api/v1/catalog`

Returns every **active seller listing** joined with its product, variant,
and seller — one ready-to-render storefront card per row.

Example response:

```json
{
  "status": "success",
  "message": "Catalog retrieved successfully",
  "data": [
    {
      "listing_id": "9f7c...-uuid",
      "price": 549.99,
      "stock": 12,
      "condition": "new",
      "product": {
        "id": "uuid",
        "name": "iPhone 15 Pro",
        "slug": "iphone-15-pro",
        "description": "...",
        "category_id": "uuid"
      },
      "variant": {
        "id": "uuid",
        "sku_code": "IP15-256-BLK",
        "attribute_values": [
          { "attribute_id": "uuid", "attribute_name": "Storage", "value": "256GB" },
          { "attribute_id": "uuid", "attribute_name": "Color", "value": "Black" }
        ]
      },
      "seller": { "id": "uuid", "business_name": "TechHub Rwanda" },
      "images": [
        { "id": "uuid", "url": "https://res.cloudinary.com/...", "is_primary": true, "sort_order": 0 }
      ]
    }
  ]
}
```

**For the storefront card**, use:
- `product.name` → title
- `images` → pictures (prefer the one where `is_primary === true`)
- `price` → price; `currency` is implicit from platform config
- `stock` → availability (grey out / disable "add to cart" when `0`)
- `seller.business_name` → shop name
- `variant.attribute_values` → small spec badges (e.g. `256GB`, `Black`)
- ⭐ **`listing_id`** → the ID you send to the cart. Store it on the card's data model.

#### Optional query params (all filter together)

| Param | Meaning |
|---|---|
| `category_id` | Only this category + all its subcategories |
| `brand_id` | Exact brand |
| `search` | Name / brand / category / variant-attribute text match |
| `min_price` / `max_price` | Price bounds |
| `condition` | `new`, `like_new`, `used` (repeat the param to select several) |
| `in_stock=true` | Only offers with stock > 0 |
| `attribute_id` + `value` | Parallel lists: `attribute_id=UUID&value=256GB&attribute_id=UUID&value=Black` (AND) |
| `sort` | `price_asc` (default) \| `price_desc` \| `newest` |

> There is **no pagination** in v1 — every matching row comes back at
> once. Fine at current scale; page-size is a backend concern, not yours.

### Product detail page — `GET /api/v1/catalog/products/{product_id}`

Use this for a product page that shows variants side-by-side and which
seller offers them:

```json
{
  "id": "uuid", "name": "...", "slug": "...", "description": "...",
  "category_id": "uuid", "brand_id": "uuid",
  "images": [ { "id": "uuid", "url": "...", "is_primary": true, "sort_order": 0 } ],
  "variants": [
    {
      "id": "uuid", "sku_code": "...",
      "attribute_values": [ { "attribute_id": "uuid", "attribute_name": "Color", "value": "Black" } ],
      "offers": [
        { "listing_id": "uuid", "price": 549.99, "stock": 12, "condition": "new",
          "seller": { "id": "uuid", "business_name": "TechHub Rwanda" } }
      ]
    }
  ]
}
```

When the buyer picks a variant **and** a seller, the corresponding
`offers[].listing_id` is what you add to the cart.

### Dynamic filter sidebar — `GET /api/v1/catalog/filters`

Returns the filter groups to render (brands, attributes with live values,
price range, conditions) for a category or the whole catalog. Feed the
returned values straight back into `GET /catalog` as query params. Render
directly from the payload — no per-category hardcoding (`category_id` +
all descendants are in `category_ids`, active brands in `brands`,
filterable attributes in `attributes[]` with their `values`, plus
`price_range` and `conditions`).

---

## 4. Cart (authenticated)

Cart is a temporary buyer-interaction mechanism — the **order** is the
permanent financial record created later at checkout.

### Add an item — `POST /api/v1/carts/items`  (201)

Auth: `Authorization: Bearer <access_token>`

```json
{
  "listing_id": "9f7c...-uuid",
  "quantity": 1
}
```

- `listing_id` is **always** taken from the catalog / detail-page offer —
  never typed by hand, never guessed.
- `quantity` must be `>= 1`.
- Only **purchasable / active** listings are accepted.
- Adding an already-present listing **bumps its quantity**.

Returns the full updated cart.

### View the cart — `GET /api/v1/carts`

Returns the caller's cart:

```json
{
  "items": [
    {
      "id": "cart-line-uuid",
      "listing_id": "9f7c...-uuid",
      "seller_id": "uuid",
      "product_name": "iPhone 15 Pro",
      "variant_name": "256GB / Black",
      "unit_price": 549.99,
      "quantity": 1,
      "subtotal": 549.99,
      "created_at": "...", "updated_at": "..."
    }
  ],
  "item_count": 1,
  "total": 549.99
}
```

`total` is the **gross** sum of subtotals (before delivery fees or taxes —
those come later at checkout).

### Change quantity — `PATCH /api/v1/carts/items/{item_id}`

Body: `{ "quantity": 2 }` (`>= 1`). `item_id` is the cart line `id`, not
the `listing_id`.

### Remove a line — `DELETE /api/v1/carts/items/{item_id}`

### Clear the cart — `DELETE /api/v1/carts`

---

## 5. End-to-end flow the UI should implement

```
1. Buyer browses:
     GET /api/v1/catalog                  → list of cards (public)
   (optional) GET /api/v1/catalog/filters → filter sidebar
   (detail)   GET /api/v1/catalog/products/{id}

2. Buyer adds to cart:
     guaranteed logged in?  no  →  redirect to login
     POST /api/v1/auth/login            → access_token
     POST /api/v1/carts/items           → { listing_id, quantity }

3. Cart view / quantity handling:
     GET  /api/v1/carts
     PATCH/DELETE /api/v1/carts/items/{item_id}
     DELETE /api/v1/carts                (clear)

4. (Next step, separate guide) Checkout:
     shipping address + payment → order creation
```

---

## 6. Key rules to remember

- Browsing the catalog is **public**. Cart is **private** (send the bearer
  token).
- Always read the envelope: the real payload is in `data`.
- `listing_id` is the single source of truth for what gets bought — keep it
  on every storefront card and product-detail offer, and pass it unchanged
  to the cart.
- Disable "Add to cart" when `stock === 0`.
- UUIDs are used everywhere — treat IDs as opaque strings, don't parse them.
- On `401`, refresh the token via `POST /api/v1/auth/refresh` and retry.
- No pagination in v1 yet; don't code a "load more" against the catalog.
- Prices are numeric decimals; format for display on the client (the API
  does not return a per-listing currency field in v1).
