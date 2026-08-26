import type { PremiumSubscription } from "../../types/premium";

interface PremiumAnalyticsProps {
  subscription: PremiumSubscription;
  daysRemaining: number;
}

export default function PremiumAnalytics({
  subscription,
  daysRemaining,
}: PremiumAnalyticsProps) {
  /*
   * ==========================================
   * NO ACTIVE PREMIUM MEMBERSHIP
   * ==========================================
   */

  if (!subscription.active || !subscription.plan) {
    return (
      <section className="py-16">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-10 text-center">

          <div className="max-w-2xl mx-auto">

            <h2 className="text-3xl font-bold text-gray-900">
              Premium Overview
            </h2>

            <p className="text-gray-500 mt-4 leading-7">
              Your Premium membership information will
              appear here once you activate a Premium plan.
            </p>

          </div>

        </div>
      </section>
    );
  }

  const benefits = subscription.plan.benefits;

  /*
   * ==========================================
   * MEMBERSHIP OVERVIEW DATA
   * ==========================================
   */

  const analytics = [
    {
      title: "Membership Plan",
      value: subscription.plan.name,
      color: "text-blue-600",
    },

    {
      title: "Days Remaining",
      value: `${daysRemaining} Days`,
      color:
        daysRemaining <= 7
          ? "text-yellow-600"
          : "text-green-600",
    },

    {
      title: "Membership Status",
      value: "Active",
      color: "text-green-600",
    },

    {
      title: "Premium Badge",
      value: benefits.premiumBadge
        ? "Eligible"
        : "Unavailable",
      color: benefits.premiumBadge
        ? "text-green-600"
        : "text-gray-500",
    },

    {
      title: "Referral Participation",
      value: benefits.referralCommissionEligible
        ? "Eligible"
        : "Not Eligible",
      color: benefits.referralCommissionEligible
        ? "text-green-600"
        : "text-gray-500",
    },

    {
      title: "Seller Commission",
      value: `${benefits.sellerCommissionRate}%`,
      color: "text-purple-600",
    },
  ];

  /*
   * ==========================================
   * PREMIUM OVERVIEW
   * ==========================================
   */

  return (
    <section className="py-20">

      {/* ==========================================
          SECTION HEADER
      ========================================== */}

      <div className="text-center max-w-3xl mx-auto mb-12">

        <span className="inline-block text-sm font-bold uppercase tracking-wider text-blue-600 mb-3">
          Membership Overview
        </span>

        <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
          Your Premium Membership
        </h2>

        <p className="text-gray-500 mt-4 leading-7">
          Monitor your Premium membership status,
          remaining time, and important account benefits.
        </p>

      </div>

      {/* ==========================================
          OVERVIEW CARDS
      ========================================== */}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">

        {analytics.map((item) => (

          <div
            key={item.title}
            className="
              bg-white
              rounded-2xl
              border
              border-gray-100
              p-7
              shadow-sm
              hover:shadow-lg
              hover:-translate-y-1
              transition-all
              duration-300
            "
          >

            <p className="text-sm font-medium text-gray-500 mb-3">
              {item.title}
            </p>

            <p
              className={`text-2xl md:text-3xl font-bold ${item.color}`}
            >
              {item.value}
            </p>

          </div>

        ))}

      </div>

      {/* ==========================================
          MEMBERSHIP INFORMATION
      ========================================== */}

      <div className="mt-10">

        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">

          <div className="mb-6">

            <h3 className="text-2xl font-bold text-gray-900">
              Membership Information
            </h3>

            <p className="text-gray-500 mt-2">
              Details about your current Premium subscription.
            </p>

          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-5">

            {/* PLAN */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Plan
              </span>

              <strong className="text-gray-900">
                {subscription.plan.name}
              </strong>

            </div>

            {/* PRICE */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Price
              </span>

              <strong className="text-gray-900">
                ${subscription.plan.price.toLocaleString()} USD
              </strong>

            </div>

            {/* DURATION */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Duration
              </span>

              <strong className="text-gray-900">
                {subscription.plan.duration} Days
              </strong>

            </div>

            {/* STATUS */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Status
              </span>

              <span className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                Active
              </span>

            </div>

            {/* START DATE */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Started
              </span>

              <strong className="text-gray-900">
                {subscription.startDate
                  ? new Date(
                      subscription.startDate
                    ).toLocaleDateString()
                  : "-"}
              </strong>

            </div>

            {/* EXPIRY DATE */}

            <div className="flex justify-between items-center border-b pb-4">

              <span className="text-gray-500">
                Expires
              </span>

              <strong className="text-gray-900">
                {subscription.expiryDate
                  ? new Date(
                      subscription.expiryDate
                    ).toLocaleDateString()
                  : "-"}
              </strong>

            </div>

          </div>

        </div>

      </div>

      {/* ==========================================
          REFERRAL ELIGIBILITY
      ========================================== */}

      {benefits.referralCommissionEligible && (

        <div className="mt-8 bg-blue-50 border border-blue-100 rounded-2xl p-6">

          <h3 className="font-bold text-blue-800 text-lg">
            Referral Commission Eligibility
          </h3>

          <p className="text-gray-600 mt-2 leading-7">
            Your Premium membership makes you eligible
            to participate in the MUHUZE referral
            commission program.
          </p>

          <p className="text-gray-600 mt-2 leading-7">
            Membership itself does not guarantee income.
            Commissions are generated only from qualifying
            referred-user activity and eligible MUHUZE
            revenue according to the referral program rules.
          </p>

        </div>

      )}

    </section>
  );
}