import {
  FaCheckCircle,
  FaTimesCircle,
  FaCrown,
} from "react-icons/fa";

import type { PremiumPlan } from "../../types/premium";

interface PremiumComparisonProps {
  plans: PremiumPlan[];
  onSelect: (plan: PremiumPlan) => void;
}

/**
 * ==========================================
 * COMPARISON FEATURE TYPE
 * ==========================================
 */

type FeatureKey =
  | "premiumBadge"
  | "priorityNotifications"
  | "earlyPromotionAccess"
  | "premiumOnlyPromotions"
  | "premiumDiscounts"
  | "enhancedFavorites"
  | "prioritySupport"
  | "enhancedVisibility"
  | "promotionalAdvantages"
  | "advancedAnalytics"
  | "unlimitedListings"
  | "sellerVerificationEligible"
  | "referralCommissionEligible";

interface ComparisonFeature {
  title: string;
  key: FeatureKey;
}

/**
 * ==========================================
 * COMPARISON FEATURES
 * ==========================================
 */

const features: ComparisonFeature[] = [
  {
    title: "Premium Member Badge",
    key: "premiumBadge",
  },
  {
    title: "Priority Notifications",
    key: "priorityNotifications",
  },
  {
    title: "Early Access to Promotions",
    key: "earlyPromotionAccess",
  },
  {
    title: "Premium-Only Promotions",
    key: "premiumOnlyPromotions",
  },
  {
    title: "Premium Member Discounts",
    key: "premiumDiscounts",
  },
  {
    title: "Enhanced Favorites / Watchlist",
    key: "enhancedFavorites",
  },
  {
    title: "Priority Customer Support",
    key: "prioritySupport",
  },
  {
    title: "Increased Product Visibility",
    key: "enhancedVisibility",
  },
  {
    title: "Seller Promotional Advantages",
    key: "promotionalAdvantages",
  },
  {
    title: "Advanced Seller Analytics",
    key: "advancedAnalytics",
  },
  {
    title: "Unlimited Product Listings",
    key: "unlimitedListings",
  },
  {
    title: "Seller Verification Eligibility",
    key: "sellerVerificationEligible",
  },
  {
    title: "Referral Commission Participation",
    key: "referralCommissionEligible",
  },
];

/**
 * ==========================================
 * FREE COMPARISON PLAN
 * ==========================================
 *
 * IMPORTANT:
 *
 * This is NOT a PremiumPlan.
 *
 * It exists only for the comparison table.
 *
 * It can never be passed to onSelect().
 */

interface FreeComparisonPlan {
  id: "free";
  name: "Free";
  price: 0;
  duration: null;
  popular: false;
  isFree: true;
}

const FREE_PLAN: FreeComparisonPlan = {
  id: "free",
  name: "Free",
  price: 0,
  duration: null,
  popular: false,
  isFree: true,
};

/**
 * ==========================================
 * COMPARISON PLAN TYPE
 * ==========================================
 */

type ComparisonPlan =
  | PremiumPlan
  | FreeComparisonPlan;

/**
 * ==========================================
 * PREMIUM COMPARISON
 * ==========================================
 */

export default function PremiumComparison({
  plans,
  onSelect,
}: PremiumComparisonProps) {

  /**
   * Free is displayed only here.
   *
   * Monthly and Annual remain the real
   * PremiumPlan objects.
   */

  const comparisonPlans: ComparisonPlan[] = [
    FREE_PLAN,
    ...plans,
  ];

  /**
   * ==========================================
   * CHECK IF PLAN IS FREE
   * ==========================================
   */

  const isFreePlan = (
  plan: ComparisonPlan
): plan is FreeComparisonPlan => {
  return "isFree" in plan && plan.isFree === true;
};

  /**
   * ==========================================
   * CHECK FEATURE
   * ==========================================
   */

  const isFeatureEnabled = (
    plan: ComparisonPlan,
    featureKey: FeatureKey
  ): boolean => {

    /**
     * Free has no Premium benefits.
     */

    if (isFreePlan(plan)) {
      return false;
    }

    return plan.benefits[featureKey];
  };

  return (
    <section className="py-20">

      {/* ==========================================
          HEADER
      ========================================== */}

      <div className="text-center mb-12">

        <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
          Compare Membership Plans
        </h2>

        <p className="text-gray-500 mt-4 max-w-2xl mx-auto">
          Start with the Free plan or upgrade to
          Premium to unlock more powerful tools and
          business opportunities on MUHUZE Global Link.
        </p>

      </div>

      {/* ==========================================
          TABLE
      ========================================== */}

      <div className="overflow-x-auto rounded-2xl shadow-xl">

        <table className="w-full min-w-[900px] border-collapse bg-white">

          {/* ========================================
              HEADER
          ======================================== */}

          <thead>

            <tr className="bg-blue-700 text-white">

              <th className="text-left p-5 min-w-[280px]">
                Features
              </th>

              {comparisonPlans.map((plan) => {

                const free =
                  isFreePlan(plan);

                return (
                  <th
                    key={plan.id}
                    className={`p-5 text-center min-w-[180px] ${
                      plan.popular
                        ? "bg-yellow-500"
                        : ""
                    }`}
                  >

                    {/* POPULAR */}

                    {plan.popular && (
                      <div className="flex items-center justify-center gap-2 text-xs mb-2 font-bold">
                        <FaCrown />
                        MOST POPULAR
                      </div>
                    )}

                    {/* NAME */}

                    <div className="text-xl font-bold">
                      {plan.name}
                    </div>

                    {/* PRICE */}

                    <div className="mt-2 text-lg font-bold">

                      {free
                        ? "$0"
                        : `$${plan.price.toLocaleString()}`}

                    </div>

                  </th>
                );
              })}

            </tr>

          </thead>

          <tbody>

            {/* ======================================
                DURATION
            ====================================== */}

            <tr className="border-b">

              <td className="p-5 font-semibold text-gray-800">
                Membership Duration
              </td>

              {comparisonPlans.map((plan) => {

                const free =
                  isFreePlan(plan);

                return (
                  <td
                    key={plan.id}
                    className={`text-center p-5 ${
                      plan.popular
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >
                    {free
                      ? "No Expiry"
                      : `${plan.duration} Days`}
                  </td>
                );
              })}

            </tr>

            {/* ======================================
                SELLER COMMISSION
            ====================================== */}

            <tr className="border-b hover:bg-gray-50">

              <td className="p-5 font-semibold text-gray-800">
                Seller Commission
              </td>

              {comparisonPlans.map((plan) => {

                const free =
                  isFreePlan(plan);

                return (
                  <td
                    key={plan.id}
                    className={`text-center p-5 ${
                      plan.popular
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >

                    {free ? (
                      <span className="text-gray-500 font-medium">
                        Standard
                      </span>
                    ) : (
                      <span className="font-bold text-blue-600">
                        {plan.benefits.sellerCommissionRate}%
                      </span>
                    )}

                  </td>
                );
              })}

            </tr>

            {/* ======================================
                PREMIUM FEATURES
            ====================================== */}

            {features.map((feature) => (

              <tr
                key={feature.key}
                className="border-b hover:bg-gray-50"
              >

                <td className="p-5 font-semibold text-gray-800">
                  {feature.title}
                </td>

                {comparisonPlans.map((plan) => {

                  const enabled =
                    isFeatureEnabled(
                      plan,
                      feature.key
                    );

                  return (
                    <td
                      key={plan.id}
                      className={`text-center p-5 ${
                        plan.popular
                          ? "bg-yellow-50"
                          : ""
                      }`}
                    >

                      {enabled ? (
                        <FaCheckCircle
                          className="mx-auto text-blue-600"
                          size={20}
                        />
                      ) : (
                        <FaTimesCircle
                          className="mx-auto text-gray-300"
                          size={20}
                        />
                      )}

                    </td>
                  );
                })}

              </tr>

            ))}

            {/* ======================================
                REFERRAL INCOME
            ====================================== */}

            <tr className="border-b">

              <td className="p-5 font-semibold text-gray-800">
                Referral Income
              </td>

              {comparisonPlans.map((plan) => {

                const free =
                  isFreePlan(plan);

                const eligible =
                  !free &&
                  plan.benefits
                    .referralCommissionEligible;

                return (
                  <td
                    key={plan.id}
                    className={`text-center p-5 text-sm ${
                      plan.popular
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >

                    {eligible ? (
                      <span className="text-green-700 font-semibold">
                        Eligible to participate
                      </span>
                    ) : (
                      <span className="text-gray-500">
                        Not available
                      </span>
                    )}

                  </td>
                );
              })}

            </tr>

            {/* ======================================
                ACTIONS
            ====================================== */}

            <tr>

              <td className="p-6"></td>

              {comparisonPlans.map((plan) => {

                const free =
                  isFreePlan(plan);

                return (
                  <td
                    key={plan.id}
                    className={`p-6 text-center ${
                      plan.popular
                        ? "bg-yellow-50"
                        : ""
                    }`}
                  >

                    {free ? (

                      <div className="px-6 py-3 rounded-xl border border-gray-300 text-gray-500 font-semibold">
                        Current Free Plan
                      </div>

                    ) : (

                      <button
                        type="button"
                        onClick={() =>
                          onSelect(plan)
                        }
                        className={`w-full px-6 py-3 rounded-xl font-bold transition active:scale-95 ${
                          plan.popular
                            ? "bg-yellow-500 hover:bg-yellow-600 text-white"
                            : "bg-blue-600 hover:bg-blue-700 text-white"
                        }`}
                      >
                        Start Membership
                      </button>

                    )}

                  </td>
                );
              })}

            </tr>

          </tbody>

        </table>

      </div>

      {/* ==========================================
          REFERRAL DISCLAIMER
      ========================================== */}

      <div className="mt-8 bg-blue-50 border border-blue-100 rounded-2xl p-6">

        <h3 className="font-bold text-blue-800">
          About Referral Commissions
        </h3>

        <p className="text-gray-600 mt-2 leading-relaxed">
          Premium membership gives eligible members
          access to the MUHUZE Global Link referral
          commission program. Membership itself does
          not guarantee income. Commissions are
          generated only from qualifying referred-user
          activity and eligible MUHUZE revenue.
        </p>

      </div>

    </section>
  );
}