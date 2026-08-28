import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PremiumPlanRequest(BaseModel):
    code: str = Field(
        min_length=1, max_length=40, description="Stable plan code, e.g. 'premium-monthly'"
    )
    name: str = Field(min_length=1, max_length=50, description="Display name, e.g. 'Monthly'")
    description: str | None = Field(
        default=None, max_length=255, description="Seller-facing blurb shown on the plan card"
    )
    price: float = Field(gt=0, description="Plan price (e.g. 10 monthly / 100 annual)")
    currency: str = Field(default="USD", min_length=3, max_length=8, description="Billing currency")
    duration_days: int = Field(gt=0, description="Term length in days (30 or 365)")
    commission_rate: float = Field(
        ge=0, le=100, description="% of each sale MUHUZE keeps while on this plan (7%)"
    )
    listing_limit: int = Field(
        default=0, ge=0, description="Max active listings (0 = unlimited)"
    )
    premium_badge: bool = Field(default=False)
    unlimited_listings: bool = Field(default=False)
    priority_notifications: bool = Field(default=False)
    early_promotion_access: bool = Field(default=False)
    premium_only_promotions: bool = Field(default=False)
    premium_discounts: bool = Field(default=False)
    enhanced_favorites: bool = Field(default=False)
    priority_support: bool = Field(default=False)
    priority_service_handling: bool = Field(default=False)
    referral_commission_eligible: bool = Field(default=False)
    enhanced_visibility: bool = Field(default=False)
    promotional_advantages: bool = Field(default=False)
    advanced_analytics: bool = Field(default=False)
    seller_verification_eligible: bool = Field(default=False)
    is_active: bool = Field(default=True, description="Whether this plan is purchasable")


class PremiumPlanUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=40)
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    duration_days: int | None = Field(default=None, gt=0)
    commission_rate: float | None = Field(default=None, ge=0, le=100)
    listing_limit: int | None = Field(default=None, ge=0)
    is_active: bool | None = Field(default=None)


class PremiumPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Plan ID")
    code: str = Field(description="Stable plan code")
    name: str = Field(description="Display name")
    description: str | None = Field(description="Seller-facing blurb")
    price: float = Field(description="Plan price")
    currency: str = Field(description="Billing currency")
    duration_days: int = Field(description="Term length in days")
    commission_rate: float = Field(
        description="% of each sale MUHUZE keeps while subscribed to this plan"
    )
    listing_limit: int = Field(description="Max active listings (0 = unlimited)")
    premium_badge: bool = Field(description="Shows the premium badge on the shop")
    unlimited_listings: bool = Field(description="No listing cap while active")
    priority_notifications: bool = Field(description="Priority notifications")
    early_promotion_access: bool = Field(description="Early promotion access")
    premium_only_promotions: bool = Field(description="Premium-only promotions")
    premium_discounts: bool = Field(description="Premium-only discounts")
    enhanced_favorites: bool = Field(description="Enhanced favorites")
    priority_support: bool = Field(description="Priority support")
    priority_service_handling: bool = Field(description="Priority service handling")
    referral_commission_eligible: bool = Field(description="May earn referral commission")
    enhanced_visibility: bool = Field(description="Boosted marketplace placement")
    promotional_advantages: bool = Field(description="Promotional advantages")
    advanced_analytics: bool = Field(description="Advanced analytics")
    seller_verification_eligible: bool = Field(description="Seller verification eligible")
    is_active: bool = Field(description="Whether this plan is purchasable")
    created_at: datetime = Field(description="When the plan was created (UTC)")
    updated_at: datetime = Field(description="When the plan was last updated (UTC)")


class SubscribeRequest(BaseModel):
    plan_id: uuid.UUID = Field(description="The premium plan to subscribe to")


class SellerSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Subscription ID")
    seller_id: uuid.UUID = Field(description="Seller this subscription belongs to")
    plan_id: uuid.UUID = Field(description="The plan that was bought")
    status: str = Field(description="'active' | 'expired' | 'cancelled'")
    commission_rate: float = Field(
        description="Snapshot of the plan's commission rate at purchase time"
    )
    starts_at: datetime = Field(description="When the subscription starts (UTC)")
    expires_at: datetime = Field(description="When the subscription expires (UTC)")
    cancelled_at: datetime | None = Field(description="When it was cancelled (UTC), if at all")


class SubscriptionStatusResponse(BaseModel):
    """What the seller-facing dashboard shows: current subscription (if
    any) plus the commission rate that currently applies to the seller's
    sales."""

    seller_id: uuid.UUID = Field(description="Seller this describes")
    is_premium: bool = Field(description="Whether the seller has an active subscription")
    commission_rate: float = Field(
        description="% of each sale MUHUZE keeps for this seller (7% premium / 12% basic)"
    )
    subscription: SellerSubscriptionResponse | None = Field(
        description="The active subscription, if premium"
    )


class PlanCommissionResponse(BaseModel):
    """A thin, reusable view of the commission a seller currently pays —
    intended to be queried at order/commission-deduction time by other
    modules (orders, revenue) that need to know whether to take 12% or 7%."""

    seller_id: uuid.UUID = Field(description="Seller this describes")
    is_premium: bool = Field(description="Whether the seller has an active subscription")
    commission_rate: float = Field(
        description="% of each sale MUHUZE keeps for this seller (7% premium / 12% basic)"
    )
