import type { PremiumPlan } from "../../types/premium";

import {
  FaCheckCircle,
  FaCrown,
} from "react-icons/fa";

interface PremiumCardProps {
  plan: PremiumPlan;
  onSelect: (plan: PremiumPlan) => void;
}

export default function PremiumCard({
  plan,
  onSelect,
}: PremiumCardProps) {
  const benefits = plan.benefits;

  return (
    <div
      className={`relative rounded-2xl border p-8 transition duration-300 flex flex-col shadow-lg hover:-translate-y-2 hover:shadow-2xl ${
        plan.popular
          ? "border-yellow-400 ring-4 ring-yellow-200 bg-gradient-to-b from-yellow-50 to-white"
          : "border-gray-200 bg-white"
      }`}
    >
      {/* ==========================================
          POPULAR LABEL
      ========================================== */}

      {plan.popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <span className="flex items-center gap-2 bg-yellow-500 text-white px-5 py-2 rounded-full font-bold shadow whitespace-nowrap">
            <FaCrown />
            MOST POPULAR
          </span>
        </div>
      )}

      {/* ==========================================
          PLAN NAME
      ========================================== */}

      <h2 className="text-3xl font-bold text-gray-800 mt-6">
        {plan.name}
      </h2>

      {/* ==========================================
          PRICE
      ========================================== */}

      <div className="mt-4">
        <p className="text-5xl font-extrabold text-blue-600">
          ${plan.price.toLocaleString()}
        </p>

        <p className="text-gray-500 mt-2">
          {plan.duration} Days Membership
        </p>

        {/* SAVINGS */}

        {plan.savings > 0 && (
          <div className="mt-3">
            <span className="inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full font-semibold">
              Save ${plan.savings.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      <div className="border-t my-8"></div>

      {/* ==========================================
          PREMIUM BENEFITS
      ========================================== */}

      <ul className="space-y-4 flex-1">

        {benefits.premiumBadge && (
          <Benefit>
            Premium Member Badge
          </Benefit>
        )}

        {benefits.priorityNotifications && (
          <Benefit>
            Priority Notifications
          </Benefit>
        )}

        {benefits.earlyPromotionAccess && (
          <Benefit>
            Early Access to Selected Promotions
          </Benefit>
        )}

        {benefits.premiumOnlyPromotions && (
          <Benefit>
            Premium-Only Promotions
          </Benefit>
        )}

        {benefits.premiumDiscounts && (
          <Benefit>
            Special Premium Member Discounts
          </Benefit>
        )}

        {benefits.enhancedFavorites && (
          <Benefit>
            Enhanced Favorites / Watchlist
          </Benefit>
        )}

        {benefits.prioritySupport && (
          <Benefit>
            Priority Customer Support
          </Benefit>
        )}

        {benefits.enhancedVisibility && (
          <Benefit>
            Increased Product Visibility
          </Benefit>
        )}

        {benefits.promotionalAdvantages && (
          <Benefit>
            Seller Promotional Advantages
          </Benefit>
        )}

        {benefits.advancedAnalytics && (
          <Benefit>
            Advanced Seller Analytics
          </Benefit>
        )}

        {benefits.unlimitedListings && (
          <Benefit>
            Unlimited Product Listings
          </Benefit>
        )}

        {benefits.sellerVerificationEligible && (
          <Benefit>
            Premium Seller Verification Eligibility
          </Benefit>
        )}

        {/* ========================================
            SELLER COMMISSION
        ======================================== */}

        <Benefit>
          {benefits.sellerCommissionRate}% Seller
          Commission
        </Benefit>

        {/* ========================================
            REFERRAL COMMISSION
        ======================================== */}

        {benefits.referralCommissionEligible && (
          <Benefit>
            Eligible for Referral Commission
            Participation
          </Benefit>
        )}

      </ul>

      {/* ==========================================
          REFERRAL NOTICE
      ========================================== */}

      {benefits.referralCommissionEligible && (
        <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl p-4">
          <p className="text-sm text-blue-800 leading-relaxed">
            Premium membership does not guarantee
            income. Referral commissions are earned
            only when qualifying referred users
            generate eligible MUHUZE revenue.
          </p>
        </div>
      )}

      {/* ==========================================
          SELECT PLAN BUTTON
      ========================================== */}

      <button
        type="button"
        onClick={() => onSelect(plan)}
        className={`mt-8 py-4 rounded-xl font-bold text-lg transition active:scale-95 ${
          plan.popular
            ? "bg-yellow-500 hover:bg-yellow-600 text-white"
            : "bg-blue-600 hover:bg-blue-700 text-white"
        }`}
      >
        Start Membership
      </button>
    </div>
  );
}

/**
 * ==========================================
 * PREMIUM BENEFIT COMPONENT
 * ==========================================
 *
 * All benefits use the same professional
 * visual language instead of different emojis.
 */

function Benefit({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <li className="flex items-start gap-3">
      <FaCheckCircle
        className="text-blue-600 mt-1 flex-shrink-0"
        size={16}
      />

      <span className="text-gray-700 leading-relaxed">
        {children}
      </span>
    </li>
  );
}