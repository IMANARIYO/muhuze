import { FaHistory } from "react-icons/fa";

import { useReferralCommission } from "../../context/ReferralCommissionContext";

import type {
  ReferralCommission,
} from "../../types/referralCommission";

export default function ReferralCommissionHistory() {
  const {
    commissions,
    loading,
    error,
  } = useReferralCommission();

  function getUserName(
    referredUser: ReferralCommission["referredUser"]
  ) {
    if (
      typeof referredUser === "string"
    ) {
      return referredUser;
    }

    return referredUser.fullName;
  }

  function getUserEmail(
    referredUser: ReferralCommission["referredUser"]
  ) {
    if (
      typeof referredUser === "string"
    ) {
      return "";
    }

    return referredUser.email;
  }

  function getStatusClass(
    status: ReferralCommission["status"]
  ) {
    switch (status) {
      case "Available":
        return "bg-green-100 text-green-700";

      case "Pending":
        return "bg-yellow-100 text-yellow-700";

      case "Reversed":
        return "bg-orange-100 text-orange-700";

      case "Cancelled":
        return "bg-red-100 text-red-700";

      default:
        return "bg-gray-100 text-gray-700";
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">
        <p className="text-center text-gray-500">
          Loading commission history...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-3xl p-6 mt-8">
        <p className="text-red-700">
          Unable to load commission history.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">
      {/* Header */}

      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center">
          <FaHistory className="text-blue-600 text-2xl" />
        </div>

        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Commission History
          </h2>

          <p className="text-gray-500">
            View commissions earned from your referral network.
          </p>
        </div>
      </div>

      {/* Empty state */}

      {commissions.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          You don't have any referral commissions yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b bg-slate-50">
                <th className="py-4 px-3">
                  User
                </th>

                <th className="py-4 px-3">
                  Level
                </th>

                <th className="py-4 px-3">
                  Rate
                </th>

                <th className="py-4 px-3">
                  Revenue
                </th>

                <th className="py-4 px-3">
                  Commission
                </th>

                <th className="py-4 px-3">
                  Status
                </th>

                <th className="py-4 px-3">
                  Date
                </th>
              </tr>
            </thead>

            <tbody>
              {commissions.map(
                (commission) => (
                  <tr
                    key={commission._id}
                    className="border-b last:border-b-0 hover:bg-slate-50"
                  >
                    {/* User */}

                    <td className="py-4 px-3">
                      <div className="font-medium text-gray-900">
                        {getUserName(
                          commission.referredUser
                        )}
                      </div>

                      {getUserEmail(
                        commission.referredUser
                      ) && (
                        <div className="text-sm text-gray-500">
                          {getUserEmail(
                            commission.referredUser
                          )}
                        </div>
                      )}
                    </td>

                    {/* Level */}

                    <td className="py-4 px-3">
                      <span
                        className="
                          inline-flex
                          rounded-full
                          bg-blue-100
                          text-blue-700
                          px-3
                          py-1
                          text-sm
                          font-medium
                        "
                      >
                        Level{" "}
                        {commission.level}
                      </span>
                    </td>

                    {/* Rate */}

                    <td className="py-4 px-3 font-semibold">
                      {commission.commissionRate}%
                    </td>

                    {/* Revenue */}

                    <td className="py-4 px-3">
                      {commission.revenueAmount.toLocaleString()}{" "}
                      {commission.currency}
                    </td>

                    {/* Commission */}

                    <td className="py-4 px-3 font-bold text-green-600">
                      {commission.commissionAmount.toLocaleString()}{" "}
                      {commission.currency}
                    </td>

                    {/* Status */}

                    <td className="py-4 px-3">
                      <span
                        className={`
                          inline-flex
                          rounded-full
                          px-3
                          py-1
                          text-sm
                          font-medium
                          ${getStatusClass(
                            commission.status
                          )}
                        `}
                      >
                        {commission.status}
                      </span>
                    </td>

                    {/* Date */}

                    <td className="py-4 px-3 text-gray-600">
                      {new Date(
                        commission.createdAt
                      ).toLocaleDateString()}
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}