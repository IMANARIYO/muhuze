# Products / Catalog Roadmap

## Phase 1 — Models + Migration (done)

- [x] SQLAlchemy models for all 9 catalog tables
- [x] Alembic migration (`82b4a38bd93b`)
- [x] Register models in `app/db/models.py`
- [x] Documentation (this folder)

## Phase 2 — Brand CRUD (admin) (done)

- [x] Brand repository, service, controller, router
- [x] `POST /api/v1/brands` — create brand (admin only)
- [x] `GET /api/v1/brands` — list all brands
- [x] `GET /api/v1/brands/{id}` — get one brand
- [x] `PATCH /api/v1/brands/{id}` — update brand (admin only)
- [x] Slug uniqueness with collision handling (same pattern as categories)
- [x] Name uniqueness (`brands.name` is DB-unique — checked in the service so
      a collision is a clean 409, not a raw `IntegrityError`)
- [x] Tests

## Phase 3 — Attribute CRUD (admin) (done — binding deferred)

- [x] Attribute repository, service, controller, router
- [x] `POST /api/v1/attributes` — create attribute (admin only)
- [x] `GET /api/v1/attributes` — list all attributes
- [x] `GET /api/v1/attributes/{id}` — get one attribute
- [x] `PATCH /api/v1/attributes/{id}` — update attribute (admin only)
- [ ] Category-attribute binding endpoints — **deferred.** `category_attributes`
      exists as a table only; attributes are freely assignable to any
      variant for now (still admin-curated, so no free-text chaos — just no
      per-category required/variant/filterable enforcement yet).
- [x] Tests

## Phase 4 — Product CRUD (admin) (done)

- [x] Product repository, service, controller, router
- [x] `POST /api/v1/products` — create product (admin only)
- [x] `GET /api/v1/products` — list products (filters: category_id, brand_id, status)
- [x] `GET /api/v1/products/{id}` — get one product
- [x] `PATCH /api/v1/products/{id}` — update product (admin only, draft/rejected only)
- [x] Full status lifecycle: submit / approve / reject (with reason) / archive
- [x] Product image upload (Cloudinary, public delivery — see database.md)
- [x] Auto-generate slug from name
- [x] Tests

## Phase 5 — Variant Management (done — generation deferred)

- [ ] Variant *auto*-generation from category's variant attributes —
      **deferred**, depends on Phase 3's category-attribute binding.
- [x] `GET /api/v1/products/{id}/variants` — list variants
- [x] `POST /api/v1/products/{id}/variants` — create variant (admin), with
      attribute values supplied directly in the request
- [x] `PATCH /api/v1/products/{id}/variants/{id}` — update sku_code/status
- [ ] `POST /api/v1/products/{id}/variants/generate` — auto-generate all
      variants — deferred with the above
- [x] Variant uniqueness enforcement (same attribute-value combination
      within a product is rejected)
- [x] Tests

## Phase 6 — Seller Listings

- [ ] Listing repository, service, controller, router
- [ ] `POST /api/v1/sellers/me/listings` — create listing (active sellers only)
- [ ] `GET /api/v1/sellers/me/listings` — list own listings
- [ ] `GET /api/v1/sellers/me/listings/{id}` — get one own listing
- [ ] `PATCH /api/v1/sellers/me/listings/{id}` — update listing (draft/rejected only)
- [ ] `POST /api/v1/sellers/me/listings/{id}/submit` — submit for review
- [ ] `PATCH /api/v1/sellers/me/listings/{id}/price` — update price (active only)
- [ ] `PATCH /api/v1/sellers/me/listings/{id}/stock` — update stock (active only)
- [ ] `POST /api/v1/sellers/me/listings/{id}/archive` — archive listing
- [ ] Listing image upload (Cloudinary)
- [ ] Admin review endpoints (approve/reject/suspend/reactivate)
- [ ] Duplicate prevention (seller_id + variant_id unique)
- [ ] Tests

## Phase 7 — Public Catalog API (buyer-facing)

- [ ] `GET /api/v1/catalog/products` — browse products (with category/brand/attribute filters)
- [ ] `GET /api/v1/catalog/products/{slug}` — product detail page
- [ ] `GET /api/v1/catalog/products/{slug}/variants` — list variants with available sellers
- [ ] `GET /api/v1/catalog/products/{slug}/sellers` — compare sellers for a product
- [ ] Category tree endpoint (with attribute metadata)
- [ ] Tests

## Phase 8 — Search (future)

- [ ] PostgreSQL full-text search on product names and descriptions
- [ ] Faceted search (filter by brand, attributes, price range)
- [ ] Search by seller availability
- [ ] Upgrade to dedicated search engine (Elasticsearch/Meilisearch) if needed

## Phase 9 — Product Requests (seller-initiated) (done — duplicate detection deferred)

- [x] `POST /api/v1/products` — now callable by an active seller too (not
      just admin), tagged via `created_by_seller_id`; same endpoint,
      widened auth via `require_admin_or_active_seller`
- [x] `GET /api/v1/products/mine` — seller's own requests, any status
- [x] `GET /api/v1/products?search=` — check for an existing product
      before requesting a new one
- [x] Ownership enforced on update/submit/variant-create/image-upload
      while draft/pending_review/rejected; opens up to any active seller
      once `active` (shared catalog)
- [x] Admin review queue — reuses the existing pending_review/approve/
      reject/archive endpoints, unchanged
- [ ] Duplicate detection (admin manually attaching a seller's request to
      an existing product instead of approving a true duplicate as a new
      one) — deferred, no tooling for it yet; admin currently either
      approves as a new product or rejects with a reason pointing the
      seller at the existing one
- [x] Tests

## Phase 10 — Advanced (much later)

- [ ] Product reviews and ratings
- [ ] Product questions and answers
- [ ] Product matching/merging (deduplication)
- [ ] Inventory management (reservations, backorders)
- [ ] Product recommendations
- [ ] Product moderation queue
