import type { User } from "../../types/user";

/**
 * ==========================================
 * PREMIUM RULES
 * ==========================================
 *
 * These rules apply to Individual Premium.
 *
 * Current plans:
 *
 * Monthly → $10
 * Annual  → $100
 *
 * Business and Enterprise will be handled
 * separately in future phases.
 */

/**
 * ==========================================
 * CHECK PREMIUM STATUS
 * ==========================================
 */

export function hasPremium(
  user: User
): boolean {
  return user.premium.active;
}

/**
 * ==========================================
 * PREMIUM BADGE
 * ==========================================
 *
 * Premium members receive a Premium badge.
 */

export function hasPremiumBadge(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .premiumBadge
  );
}

/**
 * ==========================================
 * UNLIMITED SELLER LISTINGS
 * ==========================================
 *
 * Premium sellers can have unlimited
 * product listings.
 *
 * IMPORTANT:
 *
 * This function only checks Premium status.
 * Whether the user is actually a seller
 * can be checked by the caller using role.
 */

export function hasUnlimitedListings(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .unlimitedListings
  );
}

/**
 * ==========================================
 * SELLER VERIFICATION ELIGIBILITY
 * ==========================================
 *
 * Premium does NOT automatically make
 * someone a verified seller.
 *
 * It gives eligibility for the MUHUZE
 * verification process.
 */

export function isEligibleForSellerVerification(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .sellerVerificationEligible
  );
}

/**
 * ==========================================
 * ENHANCED VISIBILITY
 * ==========================================
 *
 * Premium sellers receive enhanced
 * marketplace visibility.
 */

export function hasEnhancedVisibility(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .enhancedVisibility
  );
}

/**
 * ==========================================
 * PROMOTIONAL ADVANTAGES
 * ==========================================
 */

export function hasPromotionalAdvantages(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .promotionalAdvantages
  );
}

/**
 * ==========================================
 * ADVANCED ANALYTICS
 * ==========================================
 */

export function hasAdvancedAnalytics(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .advancedAnalytics
  );
}

/**
 * ==========================================
 * PRIORITY NOTIFICATIONS
 * ==========================================
 */

export function hasPriorityNotifications(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .priorityNotifications
  );
}

/**
 * ==========================================
 * EARLY PROMOTION ACCESS
 * ==========================================
 */

export function hasEarlyPromotionAccess(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .earlyPromotionAccess
  );
}

/**
 * ==========================================
 * PREMIUM-ONLY PROMOTIONS
 * ==========================================
 */

export function hasPremiumOnlyPromotions(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .premiumOnlyPromotions
  );
}

/**
 * ==========================================
 * PREMIUM DISCOUNTS
 * ==========================================
 */

export function hasPremiumDiscounts(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .premiumDiscounts
  );
}

/**
 * ==========================================
 * ENHANCED FAVORITES
 * ==========================================
 */

export function hasEnhancedFavorites(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .enhancedFavorites
  );
}

/**
 * ==========================================
 * PRIORITY SUPPORT
 * ==========================================
 */

export function hasPrioritySupport(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .prioritySupport
  );
}

/**
 * ==========================================
 * PRIORITY SERVICE HANDLING
 * ==========================================
 */

export function hasPriorityServiceHandling(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .priorityServiceHandling
  );
}

/**
 * ==========================================
 * REFERRAL COMMISSION ELIGIBILITY
 * ==========================================
 *
 * IMPORTANT:
 *
 * Premium membership does NOT guarantee
 * referral income.
 *
 * This only determines whether the member
 * is eligible to participate in the referral
 * commission program.
 *
 * Actual commission requires:
 *
 * Premium member
 *      ↓
 * Qualifying referred users
 *      ↓
 * Real MUHUZE economic activity
 *      ↓
 * Eligible MUHUZE revenue
 *      ↓
 * Referral commission
 */

export function canEarnReferralCommission(
  user: User
): boolean {
  return (
    user.premium.active &&
    !!user.premium.plan?.benefits
      .referralCommissionEligible
  );
}

/**
 * ==========================================
 * PREMIUM SELLER COMMISSION RATE
 * ==========================================
 *
 * Basic Seller:
 * 12%
 *
 * Premium Seller:
 * 7%
 *
 * Returns null when the user is not
 * an active Premium member.
 */

export function getPremiumSellerCommissionRate(
  user: User
): number | null {
  if (!user.premium.active) {
    return null;
  }

  const rate =
    user.premium.plan?.benefits
      .sellerCommissionRate;

  if (
    typeof rate !== "number" ||
    !Number.isFinite(rate)
  ) {
    return null;
  }

  return rate;
}

/**
 * ==========================================
 * CAN RENEW
 * ==========================================
 *
 * An active Premium subscription can be
 * renewed.
 *
 * The payment/renewal process itself must
 * be handled by the appropriate payment
 * service.
 */

export function canRenew(
  user: User
): boolean {
  return user.premium.active;
}