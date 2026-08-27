# Categories Roadmap

## Phase 1 — Model + Migration + Wired (current)

- [x] Category model with self-referencing parent_id
- [x] Model upgraded with `image` and `sort_order` fields
- [x] Full module implementation (router, controller, service, repository, schemas, exceptions, dependencies)
- [x] Wired into `app/api/v1/router.py`
- [x] Documentation (this folder)
- [ ] Alembic migration (included in catalog tables migration)

## Phase 2 — Attribute Binding (future)

- [ ] Admin endpoints to bind/unbind attributes to categories
- [ ] `POST /api/v1/categories/{id}/attributes` — bind attribute
- [ ] `DELETE /api/v1/categories/{id}/attributes/{attr_id}` — unbind
- [ ] `GET /api/v1/categories/{id}/attributes` — list bound attributes
- [ ] Validation: attribute must exist and be active

## Phase 3 — Category Move (future)

- [ ] `POST /api/v1/categories/{id}/move` — move to new parent
- [ ] Cycle prevention validation
- [ ] Validation: target parent must exist

## Phase 4 — Category Suggestions (future, seller-initiated)

- [ ] `POST /api/v1/sellers/me/category-suggestions` — suggest new category
- [ ] Admin review queue
- [ ] Approve → category created; reject → seller notified

## Phase 5 — Full Tree Endpoint (future)

- [ ] `GET /api/v1/categories/tree` — return entire category tree as nested JSON
