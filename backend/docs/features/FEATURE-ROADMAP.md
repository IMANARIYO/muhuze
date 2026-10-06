# Feature Roadmap

One row per feature, in build order (AGENTS.md §6). Statuses: `PLANNED`, `DESIGNING`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `TESTING`, `COMPLETED`, `DEPRECATED`. A feature is `COMPLETED` only when the definition of done in AGENTS.md §22 holds.

The module build order and its reasoning are in [`README.md` §17](../../../README.md#17-implementation-roadmap). A feature gets its `NNN_<feature>.md` document when work on it starts.

| # | Feature | Status | Document | Notes |
|---|---|---|---|---|
| 001 | Authentication | `TESTING` | [001_authentication.md](001_authentication.md) | Written; tests not yet run. Rate limiting outstanding. |
| 002 | Users | `PLANNED` | – | Profile editing, account deactivation. |
| 003 | Roles and permissions | `TESTING` | [003_roles_and_permissions.md](003_roles_and_permissions.md) | Written; tests not yet run. |
| 004 | Sellers | `TESTING` | [004_sellers.md](004_sellers.md) | Written and walked through against a real database; tests not yet run. A real Cloudinary upload is still to be tried. |
| 005 | Customers | `PLANNED` | – | |
| 006 | Categories | `TESTING` | [006_categories.md](006_categories.md) | Seller-owned, flat. Written and walked through against a real database; tests not yet run. Categories, attributes, and options in use cannot be deleted (enforced since products). |
| 007 | Products | `TESTING` | [007_products.md](007_products.md) | Written and walked through against a real database; tests not yet run. No stock (008) and no attribute filters for buyers yet. |
| 008 | Inventory | `PLANNED` | – | |
| 009 | Cart | `PLANNED` | – | |
| 010 | Orders | `PLANNED` | – | |
| 011 | Payments | `PLANNED` | – | |
| 012 | Wallets | `PLANNED` | – | |
| 013 | Referrals | `PLANNED` | – | |
| 014 | Notifications | `PLANNED` | – | Email sending exists (`infrastructure/notifications`); background delivery belongs here. |
| 015 | Admin | `PLANNED` | – | |
| 016 | Reporting | `PLANNED` | – | |
| 017 | Seller plans, subscriptions, and commission | `DESIGNING` | – | README build-order step 6: must exist before orders. Tables drafted in `database_schema.dbml`, awaiting review of nine proposals. Not in the original numbered list, so it takes the next free number. |
