from datetime import UTC, datetime


def utc_now() -> datetime:
    """The current time as a timezone-aware UTC datetime.

    Every timestamp in the application is created through this function and
    stored as `timestamptz`, so naive datetimes never enter the system.
    """
    return datetime.now(UTC)
