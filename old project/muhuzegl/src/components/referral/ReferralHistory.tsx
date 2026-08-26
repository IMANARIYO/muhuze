import { FaHistory } from "react-icons/fa";

import { useReferral } from "../../context/ReferralContext";

import type { Referral } from "./types";

export default function ReferralHistory() {
  const { referrals } = useReferral();

  return (
    <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center">
          <FaHistory className="text-blue-600 text-2xl" />
        </div>

        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Referral History
          </h2>

          <p className="text-gray-500">
            View the users you have referred.
          </p>
        </div>
      </div>

      {/* No referrals */}
      {referrals.length === 0 ? (
        <div className="text-center py-10 text-gray-500">
          You don't have any referrals yet.
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
                  Email
                </th>

                <th className="py-4 px-3">
                  Reward
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
              {referrals.map(
                (referral: Referral) => (
                  <tr
                    key={referral._id}
                    className="border-b last:border-b-0 hover:bg-slate-50"
                  >
                    {/* User */}

                    <td className="py-4 px-3 font-medium text-gray-900">
                      {referral.referredUser.fullName}
                    </td>

                    {/* Email */}

                    <td className="py-4 px-3 text-gray-600">
                      {referral.referredUser.email}
                    </td>

                    {/* Reward */}

                    <td className="py-4 px-3 font-semibold text-green-600">
                      {referral.reward.toLocaleString()} RWF
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
                          ${
                            referral.status ===
                            "Completed"
                              ? "bg-green-100 text-green-700"
                              : "bg-yellow-100 text-yellow-700"
                          }
                        `}
                      >
                        {referral.status}
                      </span>
                    </td>

                    {/* Date */}

                    <td className="py-4 px-3 text-gray-600">
                      {new Date(
                        referral.createdAt
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