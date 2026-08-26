import type { PremiumPlan } from "../types/premium";

export const PREMIUM_PLANS: PremiumPlan[] = [
  {
    id: 1,

    service: "premium-monthly",

    name: "Monthly",

    price: 10,

    duration: 30,

    benefits: {
      premiumBadge: true,

      priorityNotifications: true,

      earlyPromotionAccess: true,

      premiumOnlyPromotions: true,

      premiumDiscounts: true,

      enhancedFavorites: true,

      prioritySupport: true,

      priorityServiceHandling: true,

      referralCommissionEligible: true,

      enhancedVisibility: true,

      promotionalAdvantages: true,

      advancedAnalytics: true,

      unlimitedListings: true,

      sellerVerificationEligible: true,

      sellerCommissionRate: 7,
    },

    popular: false,

    savings: 0,
  },

  {
    id: 2,

    service: "premium-annual",

    name: "Annual",

    price: 100,

    duration: 365,

    benefits: {
      premiumBadge: true,

      priorityNotifications: true,

      earlyPromotionAccess: true,

      premiumOnlyPromotions: true,

      premiumDiscounts: true,

      enhancedFavorites: true,

      prioritySupport: true,

      priorityServiceHandling: true,

      referralCommissionEligible: true,

      enhancedVisibility: true,

      promotionalAdvantages: true,

      advancedAnalytics: true,

      unlimitedListings: true,

      sellerVerificationEligible: true,

      sellerCommissionRate: 7,
    },

    popular: true,

    savings: 20,
  },
];