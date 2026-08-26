import type { ServiceType } from "./payment";

/**
 * ==========================================
 * INDIVIDUAL PREMIUM PLAN TYPES
 * ==========================================
 */

export type PremiumPlanType =
  | "Monthly"
  | "Annual";

/**
 * ==========================================
 * PREMIUM BENEFITS
 * ==========================================
 */

export interface PremiumBenefits {
  premiumBadge: boolean;

  priorityNotifications: boolean;

  earlyPromotionAccess: boolean;

  premiumOnlyPromotions: boolean;

  premiumDiscounts: boolean;

  enhancedFavorites: boolean;

  prioritySupport: boolean;

  priorityServiceHandling: boolean;

  referralCommissionEligible: boolean;

  enhancedVisibility: boolean;

  promotionalAdvantages: boolean;

  advancedAnalytics: boolean;

  unlimitedListings: boolean;

  sellerVerificationEligible: boolean;

  sellerCommissionRate: number;
}

/**
 * ==========================================
 * PREMIUM PLAN
 * ==========================================
 */

export interface PremiumPlan {
  id: number;

  service: ServiceType;

  name: PremiumPlanType;

  price: number;

  duration: number;

  benefits: PremiumBenefits;

  popular: boolean;

  savings: number;
}

/**
 * ==========================================
 * PREMIUM SUBSCRIPTION
 * ==========================================
 */

export interface PremiumSubscription {
  plan: PremiumPlan | null;

  startDate: string;

  expiryDate: string;

  active: boolean;
}