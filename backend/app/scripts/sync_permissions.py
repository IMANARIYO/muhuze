"""Reconciles app/db/permissions.py::ALL_PERMISSIONS into the database.

Run during deployment (or by hand in dev), not on every app startup — sync
is a deliberate, reviewable step, especially with --remove-stale.

    python -m app.scripts.sync_permissions
    python -m app.scripts.sync_permissions --remove-stale
"""

import argparse
import asyncio

from app.core.database import AsyncSessionLocal
from app.core.permissions_sync import sync_permissions
from app.db.permissions import ALL_PERMISSIONS


async def main(*, remove_stale: bool) -> None:
    async with AsyncSessionLocal() as db:
        result = await sync_permissions(db, ALL_PERMISSIONS, remove_stale=remove_stale)
        await db.commit()

    print(f"inserted  ({len(result.inserted)}): {result.inserted}")
    print(f"updated   ({len(result.updated)}): {result.updated}")
    if remove_stale:
        print(f"removed   ({len(result.removed)}): {result.removed}")
    else:
        print(
            "removed   : skipped (pass --remove-stale to delete permissions no longer in code)"
        )
    print(f"unchanged : {len(result.unchanged)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remove-stale",
        action="store_true",
        help="Also delete permissions no longer defined in code (cascades to role_permissions).",
    )
    args = parser.parse_args()
    asyncio.run(main(remove_stale=args.remove_stale))
