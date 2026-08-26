# Users Roadmap

## Phase 1 — Profile

- [x] `Profile` model + migration (1:1 with `Account`, enforced via unique FK)
- [x] `ProfileRepository` (`get_by_account_id`, `create`, `update`)
- [x] `ProfileService` (`get_my_profile` — 404 if missing, `upsert_profile`)
- [x] `GET /api/v1/users/me`
- [x] `PUT /api/v1/users/me`
- [x] Auth-gated via `auth`'s `get_current_account` dependency; verified one account cannot read another's profile

## Not started

- [ ] Any field beyond first/last name and DOB (address, avatar, gender, nationality — none of these were settled during design; add only when a concrete requirement shows up)
- [ ] Public/limited profile view (e.g. what a buyer sees of a seller) — currently `/me` only, no concept of viewing someone else's profile at all
- [ ] Profile completeness checks (e.g. gating certain actions on "profile filled in") — not needed until something depends on it
