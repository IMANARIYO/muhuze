"""create roles and permissions tables

Creates the five tables, seeds the three system roles, and gives the buyer
role to every account that already exists.

The permissions themselves are NOT seeded here: they are defined in code and
synced into the table when the application starts (app/bootstrap.py).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-06
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copy of the system roles as of this migration. Migrations never
# import application code, which may change later.
SYSTEM_ROLES = (
    ("buyer", "Can browse and buy. Every account holds this role."),
    ("seller", "Can sell. Granted when a seller application is approved."),
    ("admin", "Platform administrator. Always holds every permission."),
)


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def _updated_at() -> sa.Column:
    return sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.false(), nullable=False),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("resource", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        _created_at(),
        _updated_at(),
        sa.PrimaryKeyConstraint("id", name="pk_permissions"),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
        sa.UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    op.create_table(
        "account_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by_account_id", sa.Uuid(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_account_roles"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_roles_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_account_roles_role_id_roles", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_account_id"],
            ["accounts.id"],
            name="fk_account_roles_granted_by_account_id_accounts",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("account_id", "role_id", name="uq_account_roles_account_id_role_id"),
    )
    op.create_index("ix_account_roles_role_id", "account_roles", ["role_id"])

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_role_permissions"),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name="fk_role_permissions_role_id_roles", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_role_permissions_permission_id_permissions",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permissions_role_id_permission_id"
        ),
    )
    op.create_index("ix_role_permissions_permission_id", "role_permissions", ["permission_id"])

    op.create_table(
        "account_permissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("permission_id", sa.Uuid(), nullable=False),
        sa.Column("granted_by_account_id", sa.Uuid(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_account_permissions"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_permissions_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name="fk_account_permissions_permission_id_permissions",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_account_id"],
            ["accounts.id"],
            name="fk_account_permissions_granted_by_account_id_accounts",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "account_id", "permission_id", name="uq_account_permissions_account_id_permission_id"
        ),
    )
    op.create_index(
        "ix_account_permissions_permission_id", "account_permissions", ["permission_id"]
    )

    op.bulk_insert(
        roles,
        [
            {"id": uuid.uuid4(), "name": name, "description": description, "is_system": True}
            for name, description in SYSTEM_ROLES
        ],
    )
    # Accounts registered before roles existed: every account is a buyer.
    op.execute(
        """
        INSERT INTO account_roles (id, account_id, role_id)
        SELECT gen_random_uuid(), accounts.id, roles.id
        FROM accounts CROSS JOIN roles
        WHERE roles.name = 'buyer'
        """
    )


def downgrade() -> None:
    op.drop_table("account_permissions")
    op.drop_table("role_permissions")
    op.drop_table("account_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
