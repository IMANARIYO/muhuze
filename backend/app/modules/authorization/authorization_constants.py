from enum import StrEnum


class SystemRole(StrEnum):
    """The roles created by the migration. They cannot be renamed or deleted."""

    BUYER = "buyer"  # every account
    SELLER = "seller"  # granted when a seller application is approved
    ADMIN = "admin"  # holds every permission, always


ROLE_NAME_MAX_LENGTH = 50
# Lowercase letters, digits, and underscores; starts with a letter.
ROLE_NAME_PATTERN = r"^[a-z][a-z0-9_]{1,49}$"
ROLE_DESCRIPTION_MAX_LENGTH = 255
