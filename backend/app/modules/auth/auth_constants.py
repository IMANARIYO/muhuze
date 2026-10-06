from enum import StrEnum


class AccountStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"  # blocked by an admin
    DEACTIVATED = "deactivated"  # closed by the owner


class VerificationPurpose(StrEnum):
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"  # designed, not sent yet (no SMS provider)


PASSWORD_MIN_LENGTH = 8
# Upper bound so a huge password can't be used to burn Argon2 CPU time.
PASSWORD_MAX_LENGTH = 128

FULL_NAME_MAX_LENGTH = 150
# E.164: "+", country code, subscriber number; 8 to 15 digits in total.
PHONE_PATTERN = r"^\+[1-9]\d{7,14}$"

USER_AGENT_MAX_LENGTH = 255
