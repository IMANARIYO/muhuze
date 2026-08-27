# Creating a Product: Admin vs. Seller

Two different people can create the same kind of `Product` row, through
the same `POST /api/v1/products` endpoint. What differs is who's allowed
to touch it afterward, and where the request starts. This doc walks
through both, end to end, with real request/response shapes.

Both scenarios assume `category_id` (and optionally `brand_id`) already
exist — see `catalog-design.md` if not.

---

## Scenario A — Admin creates the product directly

Admin is fully trusted, so there's no ownership tracking to worry about:
`created_by_seller_id` stays `null` for the whole lifecycle, and every
step below is admin-only.

```
POST /api/v1/products                       (admin)
    ↓ status = draft, created_by_seller_id = null
POST /api/v1/products/{id}/variants          (admin, repeat per variant)
    ↓
POST /api/v1/products/{id}/images            (admin, optional)
    ↓
POST /api/v1/products/{id}/submit            (admin)
    ↓ status = pending_review
POST /api/v1/products/{id}/approve           (admin)
    ↓ status = active
```

### 1. Create the product

```http
POST /api/v1/products
Authorization: Bearer <admin_access_token>

{
  "category_id": "5b1e...-cat",
  "brand_id": "9a02...-brand",
  "name": "Samsung Galaxy A15",
  "description": "6.5-inch AMOLED, 5000mAh battery"
}
```

```json
{
  "status": "success",
  "message": "Product created successfully",
  "data": {
    "id": "prod-111",
    "category_id": "5b1e...-cat",
    "brand_id": "9a02...-brand",
    "created_by_seller_id": null,
    "name": "Samsung Galaxy A15",
    "slug": "samsung-galaxy-a15",
    "status": "draft",
    "rejection_reason": null
  }
}
```

### 2. Add variants

```http
POST /api/v1/products/prod-111/variants
Authorization: Bearer <admin_access_token>

{
  "sku_code": "A15-256-BLK",
  "attribute_values": [
    { "attribute_id": "attr-color", "value": "Black" },
    { "attribute_id": "attr-storage", "value": "256GB" }
  ]
}
```

Repeat with different `attribute_values` for each combination you want
to exist (Blue/256GB, Black/128GB, ...). Two variants of the same
product can't share the exact same combination — the second attempt is
a `422`.

### 3. Submit and approve

```http
POST /api/v1/products/prod-111/submit    (admin)
POST /api/v1/products/prod-111/approve   (admin)
```

`status` goes `draft` → `pending_review` → `active`. Since admin does
both steps themselves, this is really just a formality in this
scenario — the real gate matters in Scenario B.

**Result:** a fully admin-curated product, `created_by_seller_id = null`,
`active`, ready for any seller to attach a listing to (see
`seller-listing-flow.md`).

---

## Scenario B — A seller requests the product

Same endpoints, different caller. The seller's token resolves to an
active `Seller` via `require_admin_or_active_seller`
(`app/modules/products/dependencies.py`), and the product gets tagged
with `created_by_seller_id`. From here, **ownership gates everything
until admin approves it.**

```
POST /api/v1/products                        (seller)
    ↓ status = draft, created_by_seller_id = <this seller>
PATCH /api/v1/products/{id}                   (seller, owner only)
    ↓
POST /api/v1/products/{id}/variants           (seller, owner only)
    ↓
POST /api/v1/products/{id}/images             (seller, owner only)
    ↓
POST /api/v1/products/{id}/submit             (seller, owner only)
    ↓ status = pending_review — seller can no longer edit it
POST /api/v1/products/{id}/approve            (admin)     ─┐
    or                                                      ├─ admin only
POST /api/v1/products/{id}/reject             (admin)      ─┘
    ↓
  active                    OR                rejected (editable again)
    ↓
any active seller may now add
further variants/images too
```

### 1. Search first

Before requesting anything new, check it doesn't already exist:

```http
GET /api/v1/products?search=Samsung%20Galaxy%20A15
```

If a match comes back, skip straight to adding your own listing against
its variant (see `seller-listing-flow.md`) — don't create a duplicate.
There's no automated duplicate detection yet (`roadmap.md`), so this
check is on the seller (and on admin during review).

### 2. Create the product request

```http
POST /api/v1/products
Authorization: Bearer <seller_access_token>

{
  "category_id": "5b1e...-cat",
  "name": "Samsung Galaxy A15"
}
```

```json
{
  "data": {
    "id": "prod-222",
    "created_by_seller_id": "seller-abc",
    "status": "draft"
  }
}
```

### 3. Edit / add variants — owner only

While `draft`/`pending_review`/`rejected`, only `seller-abc` (or admin)
may touch `prod-222`. A different seller trying any of the calls below
gets `403 ProductOwnershipError`:

```http
PATCH /api/v1/products/prod-222                    (seller-abc only)
POST  /api/v1/products/prod-222/variants            (seller-abc only)
POST  /api/v1/products/prod-222/images              (seller-abc only)
```

### 4. Submit for review

```http
POST /api/v1/products/prod-222/submit
Authorization: Bearer <seller_access_token>
```

`status` → `pending_review`. Now even `seller-abc` can't edit it anymore
— it's frozen pending admin's decision.

### 5. Admin decides

```http
POST /api/v1/products/prod-222/approve            (admin)
```
→ `status = active`. **From this point, ownership stops gating
anything** — any active seller (not just `seller-abc`) can now add a
new variant or image to `prod-222`, because it's real shared catalog.
That's what makes "I also have this in a color nobody's listed yet"
possible without re-requesting the whole product.

Or:

```http
POST /api/v1/products/prod-222/reject
Authorization: Bearer <admin_access_token>

{ "reason": "Duplicate of an existing Samsung Galaxy A15 — see prod-111" }
```
→ `status = rejected`, `rejection_reason` set. `seller-abc` can now
`PATCH` it again and resubmit (e.g. after being pointed at the existing
product, they'd abandon this one and go add a listing to `prod-111`
instead).

---

## The one rule that ties both scenarios together

| Caller | `created_by_seller_id` | Can edit/submit while pending? | Can add variants once `active`? |
|---|---|---|---|
| Admin | `null` | Yes, always | Yes, always |
| The requesting seller | their own id | Yes | Yes |
| Any other seller | — | No — `403` | **Yes** — active products are shared catalog |

Approve/reject/archive are never available to sellers, regardless of
who created the product — that gate is admin-only in both scenarios.
See `product-lifecycle.md` for the full status state machine and
`app/modules/products/service.py::_check_product_write_access` for the
exact rule in code.
