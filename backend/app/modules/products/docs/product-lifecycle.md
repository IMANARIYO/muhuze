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

**v1 (initial):** Only admins create products. The catalog is
admin-curated.

**v2 (planned):** Sellers can request new products. The flow:

```
Seller searches catalog → not found → "Request a new product"
    → product created with status = pending_review
    → admin reviews → approve (active) or reject
```

This prevents sellers from creating duplicate or incorrect catalog
entries. Admin review is the quality gate.

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
