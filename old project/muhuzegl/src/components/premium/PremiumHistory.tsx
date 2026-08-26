import { useEffect, useState } from "react";

import {
  premiumApiService,
  type PremiumSubscriptionResponse,
  type PremiumPayment,
} from "../../business/services/premiumApiService";

interface PremiumHistoryProps {
  userId: string;
}

export default function PremiumHistory({
  userId,
}: PremiumHistoryProps) {
  const [subscriptions, setSubscriptions] =
    useState<PremiumSubscriptionResponse[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /**
   * ==========================================
   * LOAD PREMIUM HISTORY
   * ==========================================
   */

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setLoading(true);
        setError("");

        const response =
          await premiumApiService.getPremiumHistory();

        if (response.success) {
          setSubscriptions(response.data);
        } else {
          setError(
            "Unable to load Premium payment history."
          );
        }
      } catch (err) {
        console.error(
          "Premium history error:",
          err
        );

        setError(
          "Unable to load Premium payment history."
        );
      } finally {
        setLoading(false);
      }
    };

    /**
     * We keep userId in the component contract
     * because the page already supplies it.
     *
     * Authentication determines which history
     * the backend returns.
     */

    if (userId) {
      loadHistory();
    }
  }, [userId]);

  /**
   * ==========================================
   * LOADING
   * ==========================================
   */

  if (loading) {
    return (
      <section className="mt-20">

        <div className="mb-8">
          <h2 className="text-3xl font-bold">
            Premium Payment History
          </h2>

          <p className="text-gray-500 mt-2">
            Loading your Premium membership history...
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow p-10 text-center">
          <div className="animate-pulse text-gray-500">
            Loading payment history...
          </div>
        </div>

      </section>
    );
  }

  /**
   * ==========================================
   * ERROR
   * ==========================================
   */

  if (error) {
    return (
      <section className="mt-20">

        <div className="mb-8">
          <h2 className="text-3xl font-bold">
            Premium Payment History
          </h2>

          <p className="text-gray-500 mt-2">
            View your Premium membership payments.
          </p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">

          <h3 className="text-lg font-semibold text-red-700">
            Unable to Load History
          </h3>

          <p className="text-red-600 mt-2">
            {error}
          </p>

        </div>

      </section>
    );
  }

  /**
   * ==========================================
   * EMPTY HISTORY
   * ==========================================
   */

  if (subscriptions.length === 0) {
    return (
      <section className="mt-20">

        <div className="mb-8">

          <h2 className="text-3xl font-bold">
            Premium Payment History
          </h2>

          <p className="text-gray-500 mt-2">
            View all your Premium membership payments.
          </p>

        </div>

        <div className="bg-white rounded-2xl shadow p-10 text-center">

          <h3 className="text-xl font-semibold text-gray-800">
            No Premium Payments Yet
          </h3>

          <p className="text-gray-500 mt-2">
            Your Premium membership purchases will
            appear here after you start a subscription.
          </p>

        </div>

      </section>
    );
  }

  /**
   * ==========================================
   * HISTORY TABLE
   * ==========================================
   */

  return (
    <section className="mt-20">

      {/* ========================================
          HEADER
      ======================================== */}

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-gray-900">
          Premium Payment History
        </h2>

        <p className="text-gray-500 mt-2">
          View your Premium memberships and payment
          status.
        </p>

      </div>

      {/* ========================================
          TABLE
      ======================================== */}

      <div className="overflow-x-auto rounded-2xl shadow-lg">

        <table className="w-full min-w-[950px] bg-white">

          <thead className="bg-blue-700 text-white">

            <tr>

              <th className="text-left p-4">
                Plan
              </th>

              <th className="text-left p-4">
                Amount
              </th>

              <th className="text-left p-4">
                Payment
              </th>

              <th className="text-left p-4">
                Subscription
              </th>

              <th className="text-left p-4">
                Payment Date
              </th>

              <th className="text-left p-4">
                Reference
              </th>

            </tr>

          </thead>

          <tbody>

            {subscriptions.map(
              (subscription) => {

                const payment =
                  getPayment(
                    subscription.paymentId
                  );

                return (
                  <tr
                    key={subscription._id}
                    className="border-b hover:bg-gray-50"
                  >

                    {/* =================================
                        PLAN
                    ================================= */}

                    <td className="p-4">

                      <div className="font-bold text-gray-800">
                        {subscription.plan}
                      </div>

                      <div className="text-sm text-gray-500">
                        {subscription.plan ===
                        "Monthly"
                          ? "30 Days"
                          : "365 Days"}
                      </div>

                    </td>

                    {/* =================================
                        AMOUNT
                    ================================= */}

                    <td className="p-4">

                      <div className="font-bold text-blue-600">
                        $
                        {subscription.priceUsd.toLocaleString()}
                      </div>

                      {payment?.cryptoAmount && (
                        <div className="text-sm text-gray-500 mt-1">
                          {payment.cryptoAmount}{" "}
                          {payment.cryptoCurrency}
                        </div>
                      )}

                    </td>

                    {/* =================================
                        PAYMENT STATUS
                    ================================= */}

                    <td className="p-4">

                      {payment ? (
                        <StatusBadge
                          status={payment.status}
                        />
                      ) : (
                        <SubscriptionStatusBadge
                        status={subscription.status}
                        />
                      )}

                    </td>

                    {/* =================================
                        SUBSCRIPTION STATUS
                    ================================= */}

                    <td className="p-4">

                      <SubscriptionStatusBadge
                        status={subscription.status}
                      />

                    </td>

                    {/* =================================
                        DATE
                    ================================= */}

                    <td className="p-4">

                      <div className="text-gray-700">
                        {formatDate(
                          subscription.createdAt
                        )}
                      </div>

                      {subscription.activatedAt && (
                        <div className="text-xs text-green-600 mt-1">
                          Activated{" "}
                          {formatDate(
                            subscription.activatedAt
                          )}
                        </div>
                      )}

                    </td>

                    {/* =================================
                        REFERENCE
                    ================================= */}

                    <td className="p-4">

                      {payment?.providerPaymentId ? (
                        <div
                          className="font-mono text-xs text-gray-600 max-w-[150px] truncate"
                          title={
                            payment.providerPaymentId
                          }
                        >
                          {payment.providerPaymentId}
                        </div>
                      ) : (
                        <span className="text-gray-400">
                          —
                        </span>
                      )}

                    </td>

                  </tr>
                );
              }
            )}

          </tbody>

        </table>

      </div>

      {/* ========================================
          PAYMENT INFORMATION
      ======================================== */}

      <div className="mt-6 bg-blue-50 border border-blue-100 rounded-2xl p-6">

        <h3 className="font-bold text-blue-800">
          Payment Information
        </h3>

        <p className="text-gray-600 mt-2 leading-relaxed">
          Premium payments are processed securely
          through Muhuze Global Ink. Your membership becomes
          active only after the payment has been
          successfully confirmed.
        </p>

      </div>

    </section>
  );
}

/**
 * ==========================================
 * GET PAYMENT
 * ==========================================
 *
 * paymentId can be:
 *
 * string
 * PremiumPayment
 * null
 */

function getPayment(
  paymentId:
    | string
    | PremiumPayment
    | null
): PremiumPayment | null {

  if (!paymentId) {
    return null;
  }

  if (
    typeof paymentId === "object"
  ) {
    return paymentId;
  }

  return null;
}

/**
 * ==========================================
 * FORMAT DATE
 * ==========================================
 */

function formatDate(
  date?: string | null
) {
  if (!date) {
    return "—";
  }

  return new Date(date).toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    }
  );
}

/**
 * ==========================================
 * PAYMENT STATUS BADGE
 * ==========================================
 */

function StatusBadge({
  status,
}: {
  status: PremiumPayment["status"];
}) {

  const styles = {
    Pending:
      "bg-yellow-100 text-yellow-700",

    Processing:
      "bg-blue-100 text-blue-700",

    PartiallyPaid:
      "bg-orange-100 text-orange-700",

    Confirmed:
      "bg-green-100 text-green-700",

    Failed:
      "bg-red-100 text-red-700",

    Cancelled:
      "bg-gray-100 text-gray-600",

    Refunded:
      "bg-purple-100 text-purple-700",
  };

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
        styles[status]
      }`}
    >
      {status}
    </span>
  );
}

/**
 * ==========================================
 * SUBSCRIPTION STATUS BADGE
 * ==========================================
 */

function SubscriptionStatusBadge({
  status,
}: {
  status:
    | "Pending"
    | "Active"
    | "Expired"
    | "Cancelled";
}) {

  const styles = {
    Pending:
      "bg-yellow-100 text-yellow-700",

    Active:
      "bg-green-100 text-green-700",

    Expired:
      "bg-gray-100 text-gray-600",

    Cancelled:
      "bg-red-100 text-red-700",
  };

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${
        styles[status]
      }`}
    >
      {status}
    </span>
  );
}