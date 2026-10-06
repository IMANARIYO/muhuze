# Feature Roadmap

One row per feature, in build order (AGENTS.md §6). Statuses: `PLANNED`, `DESIGNING`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `TESTING`, `COMPLETED`, `DEPRECATED`. A feature is `COMPLETED` only when the definition of done in AGENTS.md §22 holds.

The module build order and its reasoning are in [`README.md` §17](../../../README.md#17-implementation-roadmap). A feature gets its `NNN_<feature>.md` document when work on it starts.

| # | Feature | Status | Document | Notes |
|---|---|---|---|---|
| 001 | Authentication | `TESTING` | [001_authentication.md](001_authentication.md) | Written; tests not yet run. Rate limiting outstanding. |
| 002 | Users | `PLANNED` | – | Profile editing, account deactivation. |
| 003 | Roles and permissions | `DESIGNING` | – | Tables designed in `database_schema.dbml`. Must backfill `buyer` onto existing accounts. |
| 004 | Sellers | `PLANNED` | – | |
| 005 | Customers | `PLANNED` | – | |
| 006 | Categories | `PLANNED` | – | |
| 007 | Products | `PLANNED` | – | |
| 008 | Inventory | `PLANNED` | – | |
| 009 | Cart | `PLANNED` | – | |
| 010 | Orders | `PLANNED` | – | |
| 011 | Payments | `PLANNED` | – | |
| 012 | Wallets | `PLANNED` | – | |
| 013 | Referrals | `PLANNED` | – | |
| 014 | Notifications | `PLANNED` | – | Email sending exists (`infrastructure/notifications`); background delivery belongs here. |
| 015 | Admin | `PLANNED` | – | |
| 016 | Reporting | `PLANNED` | – | |
