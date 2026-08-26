import type { PremiumPlan } from "../../types/premium";

interface PremiumHeroProps {
  plans: PremiumPlan[];
  onSelect: (plan: PremiumPlan) => void;
}

export default function PremiumHero({
  plans,
  onSelect,
}: PremiumHeroProps) {
  const monthlyPlan = plans.find(
    (plan) => plan.name === "Monthly"
  );

  const annualPlan = plans.find(
    (plan) => plan.name === "Annual"
  );

  return (
    <section className="relative overflow-hidden bg-gradient-to-r from-blue-700 to-indigo-700 text-white rounded-2xl p-8 md:p-10 mb-10 shadow-xl">

      {/* ==========================================
          DECORATIVE BACKGROUND
      ========================================== */}

      <div className="absolute -top-20 -right-20 w-64 h-64 bg-white/10 rounded-full" />

      <div className="absolute -bottom-24 -left-16 w-72 h-72 bg-blue-400/10 rounded-full" />

      {/* ==========================================
          CONTENT
      ========================================== */}

      <div className="relative max-w-4xl">

        {/* PREMIUM LABEL */}

        <span className="inline-block bg-yellow-400 text-black font-bold px-5 py-2 rounded-full mb-5 shadow-md">
          MUHUZE PREMIUM
        </span>

        {/* TITLE */}

        <h1 className="text-3xl md:text-5xl font-bold mb-5 leading-tight">
          Grow Your Business Faster
        </h1>

        {/* DESCRIPTION */}

        <p className="text-base md:text-lg text-blue-100 leading-8 mb-8 max-w-3xl">
          Upgrade to Premium and unlock powerful tools designed
          to help your business grow faster on MUHUZE Global Link.
          Enjoy unlimited product listings, priority visibility,
          premium promotions, seller benefits, referral commission
          eligibility, and more.
        </p>

        {/* ==========================================
            PREMIUM HIGHLIGHTS
        ========================================== */}

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8 max-w-3xl">

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <p className="font-bold text-lg">
              Unlimited
            </p>

            <p className="text-sm text-blue-100">
              Product Listings
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <p className="font-bold text-lg">
              Priority
            </p>

            <p className="text-sm text-blue-100">
              Business Visibility
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/10">
            <p className="font-bold text-lg">
              Referral
            </p>

            <p className="text-sm text-blue-100">
              Commission Eligibility
            </p>
          </div>

        </div>

        {/* ==========================================
            PLAN BUTTONS
        ========================================== */}

        <div className="flex flex-col sm:flex-row gap-4">

          {/* MONTHLY */}

          {monthlyPlan && (
            <button
              type="button"
              onClick={() =>
                onSelect(monthlyPlan)
              }
              className="bg-white text-blue-700 font-bold px-7 py-3 rounded-lg hover:bg-gray-100 active:scale-95 transition shadow-md"
            >
              Choose Monthly
            </button>
          )}

          {/* ANNUAL */}

          {annualPlan && (
            <button
              type="button"
              onClick={() =>
                onSelect(annualPlan)
              }
              className="bg-yellow-400 text-black font-bold px-7 py-3 rounded-lg hover:bg-yellow-300 active:scale-95 transition shadow-md"
            >
              Choose Annual
            </button>
          )}

        </div>

        {/* SMALL NOTE */}

        <p className="text-xs text-blue-200 mt-5">
          Secure cryptocurrency payments powered by NOWPayments.
        </p>

      </div>

    </section>
  );
}