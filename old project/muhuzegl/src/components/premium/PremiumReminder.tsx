import { Link } from "react-router-dom";

interface PremiumReminderProps {
  active: boolean;
  daysRemaining: number;
  onRenew?: () => void;
}

export default function PremiumReminder({
  active,
  daysRemaining,
  onRenew,
}: PremiumReminderProps) {

  /* ==========================================
     NOT PREMIUM
  ========================================== */

  if (!active) {
    return (
      <section className="my-10">

        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6 md:p-7 flex flex-col md:flex-row md:items-center md:justify-between gap-6">

          <div>

            <span className="inline-block text-xs font-bold uppercase tracking-wide text-blue-600 mb-2">
              Premium Membership
            </span>

            <h2 className="text-2xl font-bold text-gray-900">
              Grow Your Business with Premium
            </h2>

            <p className="text-gray-600 mt-2 leading-7 max-w-2xl">
              Upgrade to access increased product visibility,
              unlimited listings, seller analytics, verification
              eligibility, and priority support.
            </p>

          </div>

          <Link
            to="/premium"
            className="inline-flex justify-center bg-blue-600 hover:bg-blue-700 text-white px-7 py-3 rounded-xl font-semibold transition whitespace-nowrap"
          >
            Upgrade Now
          </Link>

        </div>

      </section>
    );
  }

  /* ==========================================
     EXPIRED
  ========================================== */

  if (daysRemaining <= 0) {
    return (
      <section className="my-10">

        <div className="bg-red-50 border border-red-100 rounded-2xl p-6 md:p-7 flex flex-col md:flex-row md:items-center md:justify-between gap-6">

          <div>

            <span className="inline-block text-xs font-bold uppercase tracking-wide text-red-600 mb-2">
              Membership Expired
            </span>

            <h2 className="text-2xl font-bold text-gray-900">
              Your Premium Membership Has Expired
            </h2>

            <p className="text-gray-600 mt-2 leading-7">
              Renew your membership to continue enjoying
              Premium benefits on MUHUZE Global Link.
            </p>

          </div>

          <button
            type="button"
            onClick={onRenew}
            disabled={!onRenew}
            className="inline-flex justify-center bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-7 py-3 rounded-xl font-semibold transition whitespace-nowrap"
          >
            Renew Membership
          </button>

        </div>

      </section>
    );
  }

  /* ==========================================
     EXPIRING SOON
  ========================================== */

  if (daysRemaining <= 7) {
    return (
      <section className="my-10">

        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl p-6 md:p-7 flex flex-col md:flex-row md:items-center md:justify-between gap-6">

          <div>

            <span className="inline-block text-xs font-bold uppercase tracking-wide text-yellow-700 mb-2">
              Renewal Reminder
            </span>

            <h2 className="text-2xl font-bold text-gray-900">
              Premium Expiring Soon
            </h2>

            <p className="text-gray-600 mt-2 leading-7">
              Your Premium membership expires in{" "}
              <strong className="text-yellow-700">
                {daysRemaining}
              </strong>{" "}
              day{daysRemaining !== 1 ? "s" : ""}.
              Renew to avoid interruption.
            </p>

          </div>

          <button
            type="button"
            onClick={onRenew}
            disabled={!onRenew}
            className="inline-flex justify-center bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-7 py-3 rounded-xl font-semibold transition whitespace-nowrap"
          >
            Renew Membership
          </button>

        </div>

      </section>
    );
  }

  /* ==========================================
     ACTIVE
  ========================================== */

  return (
    <section className="my-10">

      <div className="bg-green-50 border border-green-100 rounded-2xl p-6 md:p-7">

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">

          <div>

            <span className="inline-flex items-center text-xs font-bold uppercase tracking-wide text-green-700 mb-2">

              <span className="w-2 h-2 rounded-full bg-green-500 mr-2" />

              Membership Active

            </span>

            <h2 className="text-2xl font-bold text-gray-900">
              Your Premium Membership Is Active
            </h2>

            <p className="text-gray-600 mt-2 leading-7">
              You have{" "}
              <strong className="text-green-700">
                {daysRemaining}
              </strong>{" "}
              day{daysRemaining !== 1 ? "s" : ""} remaining
              on your current Premium membership.
            </p>

          </div>

          <div className="px-5 py-3 bg-white border border-green-100 rounded-xl text-center">

            <p className="text-xs text-gray-500 uppercase tracking-wide">
              Remaining
            </p>

            <p className="text-2xl font-bold text-green-700">
              {daysRemaining}
            </p>

            <p className="text-xs text-gray-500">
              days
            </p>

          </div>

        </div>

      </div>

    </section>
  );
}