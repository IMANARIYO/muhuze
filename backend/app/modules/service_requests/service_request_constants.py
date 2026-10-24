from enum import StrEnum


class ServiceRequestStatus(StrEnum):
    """A buyer's request for a service, before there is anything to pay
    (README §7.5). What happens after acceptance is the order's status."""

    REQUESTED = "requested"  # waiting for the provider to answer
    ACCEPTED = "accepted"  # the provider agreed; an order now exists for the buyer to pay
    DECLINED = "declined"  # the provider said no, with a reason the buyer sees
    CANCELLED = "cancelled"  # the buyer withdrew it before an answer
