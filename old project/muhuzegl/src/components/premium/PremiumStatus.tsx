import type { PremiumSubscription } from "../../types/premium";

interface PremiumStatusProps {
  subscription: PremiumSubscription;
  daysRemaining: number;
  onRenew: () => void;
}

export default function PremiumStatus({
  subscription,
  daysRemaining,
  onRenew,
}: PremiumStatusProps) {
  const isActive = subscription.active;

  return (
    <section className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 mb-10">

      {/* ==========================================
          HEADER
      ========================================== */}

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">

        <div>

          {/* STATUS */}
          <span
            className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold mb-4 ${
              isActive
                ? "bg-green-50 text-green-700 border border-green-100"
                : "bg-gray-100 text-gray-600 border border-gray-200"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full mr-2 ${
                isActive
                  ? "bg-green-500"
                  : "bg-gray-400"
              }`}
            />

            {isActive
              ? "Premium Active"
              : "Premium Inactive"}
          </span>

          {/* PLAN */}
          <h2 className="text-3xl font-bold text-gray-900">
            {subscription.plan?.name ??
              "No Active Plan"}
          </h2>

          <p className="text-gray-600 mt-3 max-w-2xl leading-7">
            Manage your Premium membership,
            monitor your subscription period, and
            continue enjoying your MUHUZE business
            benefits.
          </p>

        </div>

        {/* RENEW BUTTON */}

        <button
          type="button"
          onClick={onRenew}
          className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-xl font-semibold transition shadow-sm hover:shadow-md whitespace-nowrap"
        >
          Renew Membership
        </button>

      </div>

      {/* ==========================================
          MEMBERSHIP INFORMATION
      ========================================== */}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-10">

        {/* START DATE */}

        <div className="bg-slate-50 border border-gray-100 rounded-xl p-6">

          <p className="text-gray-500 text-sm font-medium">
            Membership Started
          </p>

          <h3 className="text-xl font-semibold text-gray-900 mt-2">
            {formatDate(
              subscription.startDate
            )}
          </h3>

        </div>

        {/* EXPIRY DATE */}

        <div className="bg-slate-50 border border-gray-100 rounded-xl p-6">

          <p className="text-gray-500 text-sm font-medium">
            Membership Expires
          </p>

          <h3 className="text-xl font-semibold text-gray-900 mt-2">
            {formatDate(
              subscription.expiryDate
            )}
          </h3>

        </div>

        {/* DAYS REMAINING */}

        <div
          className={`rounded-xl p-6 border ${
            isActive && daysRemaining > 7
              ? "bg-blue-50 border-blue-100"
              : isActive
              ? "bg-yellow-50 border-yellow-100"
              : "bg-gray-50 border-gray-100"
          }`}
        >

          <p className="text-gray-500 text-sm font-medium">
            Days Remaining
          </p>

          <h3
            className={`text-3xl font-bold mt-2 ${
              isActive && daysRemaining > 7
                ? "text-blue-700"
                : isActive
                ? "text-yellow-700"
                : "text-gray-500"
            }`}
          >
            {isActive
              ? Math.max(daysRemaining, 0)
              : 0}
          </h3>

        </div>

      </div>

    </section>
  );
}

/**
 * ==========================================
 * FORMAT DATE
 * ==========================================
 */

function formatDate(
  date: string | null
) {
  if (!date) {
    return "-";
  }

  const parsedDate = new Date(date);

  if (Number.isNaN(parsedDate.getTime())) {
    return "-";
  }

  return parsedDate.toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );
}