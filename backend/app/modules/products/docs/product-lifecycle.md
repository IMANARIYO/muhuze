# Product Lifecycle

## States

`ProductStatus` (`app/modules/products/models.py`):

| Status | Meaning |
|---|---|
| `draft` | Product created, not yet submitted. Editable. |
| `pending_review` | Submitted, awaiting admin approval. **Not editable.** |
| `active` | Approved. Visible in the marketplace catalog. Buyers can find it. |
| `rejected` | Admin declined the product. Editable again for resubmission. |
| `archived` | No longer actively listed. Not visible to buyers. |

## Transitions

```
                     admin_create()
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
                  │
         archive()
                  │
                  ▼
              ARCHIVED
```

Every transition is enforced in `ProductService` by checking the current
status before mutating. Wrong-state transitions raise specific exceptions.

## Who can create products

Both admins and active sellers — gated by
`require_admin_or_active_seller` (`app/modules/products/dependencies.py`),
which resolves the caller to either "admin" (unrestricted) or "this
specific active seller." A product created by a seller is tagged via
`Product.created_by_seller_id`; admin-created products leave it `null`.

**Ownership only matters before approval.** While a product is
`draft`/`pending_review`/`rejected`, only its requesting seller (or
admin) can edit it, submit it, or add variants/images to it — checked in
`ProductService._check_owner` / `_check_product_write_access`. The
intended flow:

```
Seller searches catalog (GET /products?search=...) → not found
    → POST /products (tagged with created_by_seller_id)
    → seller edits while draft/rejected, then POST /{id}/submit
    → admin reviews → approve (active) or reject (reason, editable again)
```

Admin can always create directly too — `created_by_seller_id` stays
`null`, immediately fully theirs, same as before this flow existed.

**Ownership stops gating once a product is `active`.** At that point
it's shared catalog — any active seller (not just the original
requester) can add new variants or images to it, which is what makes "I
also have this in Blue" possible for a variant nobody's defined yet. See
`GET /products/mine` for a seller to see their own requests (any
status, including ones nobody else can see) and `attributes-and-variants.md`
for how variants themselves work.

## Product vs. Listing status

A product can be `active` while a particular seller's listing is
`suspended` or `rejected`. These are independent lifecycles:

```
Product: ACTIVE
   │
   └── Variant: White / 42
          │
          ├── Seller A listing → ACTIVE
          ├── Seller B listing → REJECTED
          └── Seller C listing → SUSPENDED
```

The product being active means it exists in the catalog. A listing being
active means that specific seller is currently offering it.

## Editability

Only `draft` and `rejected` allow product edits (name, description,
images, category, brand). `pending_review`, `active`, and `archived` are
read-only for the creating party.

**Why:** Once submitted, the information under review shouldn't change. Once
active, changing the canonical product definition would affect all sellers
listing that product.

## Archiving

Archiving is the soft-deactivation of a product. An archived product:

- Is not visible in buyer search results
- Does not appear in new listing creation flows
- Existing seller listings may remain active (they reference the variant,
  not the product status directly)
- Can be reactivated by admin

## Relationship to listing lifecycle

Product lifecycle affects what sellers can do:

| Product Status | Seller Can Create Listing? |
|---|---|
| `draft` | No (product not in catalog) |
| `pending_review` | No (product not yet approved) |
| `active` | Yes (product is in the catalog) |
| `rejected` | No (product not approved) |
| `archived` | No (product archived) |

A seller creating a listing for a product that gets archived or rejected
after the listing was created — the listing continues to exist but may be
suppressed in search results depending on business rules.
