"""Mobile-money gateway boundary for payments.

v1 ships a **stub** implementation: `request_payment` immediately returns a
synthetic `request_reference` and `confirm_payment` treats any pending request
as cleared. The live system must swap in a real Airtel Money (MTN MoMo)
adapter behind the same `MomoGateway` protocol — nothing in the payment
service or above changes, only this file's factory.

The caller owns `payer_id` / `payee_id`: for Airtel Money these are the
mobile wallet numbers. `payer_phone` is who is charged; `provider_ref` and the
`request_reference` are the gateway's own identifiers.
"""

import uuid
from typing import Protocol


class MomoGateway(Protocol):
    def request_payment(
        self,
        *,
        amount: float,
        currency: str,
        payer_phone: str | None,
        payee_phone: str | None,
    ) -> str:
        """Ask the operator to push a payment request. Returns the gateway's
        request reference (HTTP-level, synchronous contract for the stub)."""
        ...

    def confirm_payment(self, request_reference: str) -> bool:
        """True once the operator confirms the money has cleared for the given
        request reference (the provider-callback equivalent)."""
        ...


class StubMomoGateway:
    """Deterministic stand-in gateway: requests always succeed with a fresh
    reference; any existing request confirms as paid. Enough to drive the
    create -> callback flow end-to-end and to write deterministic tests."""

    def request_payment(
        self,
        *,
        amount: float,
        currency: str,
        payer_phone: str | None,
        payee_phone: str | None,
    ) -> str:
        return f"MOMO-{uuid.uuid4().hex[:12].upper()}"

    def confirm_payment(self, request_reference: str) -> bool:
        return bool(request_reference)


def get_momo_gateway() -> MomoGateway:
    """Factory the payment service uses. Swap the implementation here for a
    real adapter without touching the service."""
    return StubMomoGateway()
