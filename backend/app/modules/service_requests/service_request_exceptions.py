from app.shared.exceptions.application_exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
)


class ServiceRequestNotFoundError(NotFoundError):
    message = "Service request not found"


class ServiceNotFoundError(NotFoundError):
    message = "Service not found"


class NotAServiceError(BusinessRuleError):
    message = "This listing is a product. Add it to your cart and check out instead."


class OwnServiceRequestError(BusinessRuleError):
    message = "You cannot request a service from your own shop"


class ScheduledTimeInPastError(BusinessRuleError):
    message = "The time for the service must be in the future"


class ServiceNoLongerOfferedError(BusinessRuleError):
    message = "This service is not on offer right now. Publish it again to accept the request."


class ServiceRequestStatusConflictError(ConflictError):
    message = "This action is not allowed in the request's current status"
