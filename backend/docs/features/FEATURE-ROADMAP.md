# Feature Roadmap

One row per feature, in build order (AGENTS.md §6). Statuses: `PLANNED`, `DESIGNING`, `IN_PROGRESS`, `BLOCKED`, `REVIEW`, `TESTING`, `COMPLETED`, `DEPRECATED`. A feature is `COMPLETED` only when the definition of done in AGENTS.md §22 holds.

The module build order and its reasoning are in [`README.md` §17](../../../README.md#17-implementation-roadmap). A feature gets its `NNN_<feature>.md` document when work on it starts.

| # | Feature | Status | Document | Notes |
|---|---|---|---|---|
| 001 | Authentication | `COMPLETED` | [001_authentication.md](001_authentication.md) | 425-test suite passes. Rate limiting outstanding. |
| 002 | Users | `PLANNED` | – | Profile editing, account deactivation. |
| 003 | Roles and permissions | `COMPLETED` | [003_roles_and_permissions.md](003_roles_and_permissions.md) | 425-test suite passes. |
| 004 | Sellers | `COMPLETED` | [004_sellers.md](004_sellers.md) | Written and walked through against a real database; 425-test suite passes. A real Cloudinary upload is still to be tried. |
| 005 | Customers | `PLANNED` | – | |
| 006 | Categories | `COMPLETED` | [006_categories.md](006_categories.md) | Seller-owned, flat. Written and walked through against a real database; 425-test suite passes. Categories, attributes, and options in use cannot be deleted (enforced since products). |
| 007 | Products | `COMPLETED` | [007_products.md](007_products.md) | Written and walked through against a real database; 425-test suite passes. No stock (008) and no attribute filters for buyers yet. |
| 008 | Inventory | `DEPRECATED` | – | **Not building it** (decided 2026-10-07, README §20 `K3`): MUHUZE does not track stock. A seller publishes a product to sell it and archives it when it is no longer available. |
| 009 | Cart | `DEPRECATED` | – | **Not building it** (decided 2026-10-07, README §20 `X8`): the cart lives in the frontend. Checkout sends product ids and quantities to orders. |
| 010 | Orders | `COMPLETED` | [010_orders.md](010_orders.md) | Written and walked through against a real database; 425-test suite passes. Refunds for rejected parts are manual. |
| 011 | Payments | `COMPLETED` | [011_payments.md](011_payments.md) | Phase 1 (manual) written and walked through against a real database; 425-test suite passes. No gateway and no refunds. |
| 012 | Wallets | `COMPLETED` | [012_wallets.md](012_wallets.md) | Revenue records and ledger-backed seller wallets written and walked through against a real database; 425-test suite passes. Read-only API. No withdrawals, refunds, or manual corrections yet. |
| 013 | Referrals | `PLANNED` | – | |
| 014 | Notifications | `PLANNED` | – | Email sending exists (`infrastructure/notifications`); background delivery belongs here. |
| 015 | Admin | `PLANNED` | – | |
| 016 | Reporting | `PLANNED` | – | |
| 017 | Seller plans, subscriptions, and commission | `COMPLETED` | [017_seller_plans.md](017_seller_plans.md) | README build-order step 6: must exist before orders. Written and walked through against a real database; 425-test suite passes. Payment for subscriptions waits for 011 (now done). Not in the original numbered list, so it took the next free number. |
| 018 | Withdrawals and payout destinations | `IN_PROGRESS` | [018_withdrawals.md](018_withdrawals.md) | README build-order step 12. Decisions `W3`–`W6`, `W8`, `W9`, `S2` recorded 2026-10-08. Implemented; tests+API docs ready for the user's test run. |
