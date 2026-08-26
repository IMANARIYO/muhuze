import type { PremiumPlan } from "../../types/premium";

/**
 * ==========================================
 * MUHUZE INDIVIDUAL PREMIUM PLANS
 * ==========================================
 *
 * Current Individual Premium plans:
 *
 * Monthly → $10 / 30 days
 * Annual  → $100 / 365 days
 *
 * Business and Enterprise are intentionally
 * NOT included here.
 *
 * They will be developed later as separate
 * membership levels.
 */

export const PREMIUM_PLANS: PremiumPlan[] = [
  /**
   * ========================================
   * INDIVIDUAL PREMIUM — MONTHLY
   * ========================================
   */

  {
    id: 1,

    /**
     * Internal payment/service identifier.
     */

    service: "premium-monthly",

    name: "Monthly",

    /**
     * $10 USD
     */

    price: 10,

    /**
     * 30 days
     */

    duration: 30,

    /**
     * ======================================
     * PREMIUM BENEFITS
     * ======================================
     */

    benefits: {
      /**
       * Buyer + Seller benefits
       */

      premiumBadge: true,

      priorityNotifications: true,

      earlyPromotionAccess: true,

      premiumOnlyPromotions: true,

      premiumDiscounts: true,

      enhancedFavorites: true,

      prioritySupport: true,

      priorityServiceHandling: true,

      /**
       * Premium members may participate
       * in the referral commission system.
       *
       * This does NOT guarantee income.
       */

      referralCommissionEligible: true,

      /**
       * Seller benefits
       */

      enhancedVisibility: true,

      promotionalAdvantages: true,

      advancedAnalytics: true,

      unlimitedListings: true,

      /**
       * Premium does not automatically
       * make a seller verified.
       *
       * It gives eligibility for the
       * MUHUZE verification process.
       */

      sellerVerificationEligible: true,

      /**
       * Premium Seller commission:
       *
       * Basic Seller = 12%
       * Premium Seller = 7%
       */

      sellerCommissionRate: 7,
    },

    popular: false,

    /**
     * Monthly has no annual saving.
     */

    savings: 0,
  },

  /**
   * ========================================
   * INDIVIDUAL PREMIUM — ANNUAL
   * ========================================
   */

  {
    id: 2,

    /**
     * Internal payment/service identifier.
     */

    service: "premium-annual",

    name: "Annual",

    /**
     * $100 USD
     */

    price: 100,

    /**
     * 365 days
     */

    duration: 365,

    /**
     * ======================================
     * PREMIUM BENEFITS
     * ======================================
     */

    benefits: {
      /**
       * Buyer + Seller benefits
       */

      premiumBadge: true,

      priorityNotifications: true,

      earlyPromotionAccess: true,

      premiumOnlyPromotions: true,

      premiumDiscounts: true,

      enhancedFavorites: true,

      prioritySupport: true,

      priorityServiceHandling: true,

      /**
       * Referral commission eligibility.
       *
       * Actual commission requires
       * qualifying economic activity.
       */

      referralCommissionEligible: true,

      /**
       * Seller benefits
       */

      enhancedVisibility: true,

      promotionalAdvantages: true,

      advancedAnalytics: true,

      unlimitedListings: true,

      sellerVerificationEligible: true,

      /**
       * Premium Seller commission = 7%
       */

      sellerCommissionRate: 7,
    },

    /**
     * Annual is the recommended/value plan.
     */

    popular: true,

    /**
     * $10 × 12 = $120
     * Annual = $100
     *
     * Saving = $20
     */

    savings: 20,
  },
];