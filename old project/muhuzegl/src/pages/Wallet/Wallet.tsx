import {
  useEffect,
  useState,
} from "react";

import Container from "../../components/ui/Container";

import { useWallet } from "../../context/WalletContext";
import { useAuth } from "../../context/AuthContext";

import WithdrawalForm from "../../components/wallet/WithdrawalForm";

import type { Withdrawal } from "../../types/withdrawal";

import { WithdrawalService } from "../../business/services/withdrawalService";

export default function WalletPage() {
  const { currentUser } = useAuth();

  const {
  balance,
  pendingBalance,
  totalEarned,
  totalWithdrawn,
  currency,
  transactions,
  loading,
  refreshWallet,
} = useWallet();

  const [withdrawals, setWithdrawals] =
    useState<Withdrawal[]>([]);

  const [
    withdrawalsLoading,
    setWithdrawalsLoading,
  ] = useState(true);

  /**
   * ==========================================
   * LOAD WITHDRAWALS
   * ==========================================
   */
useEffect(() => {
  if (!currentUser) {
    setWithdrawalsLoading(false);
    return;
  }

  const userId = currentUser._id;

  if (!userId) {
    setWithdrawalsLoading(false);
    return;
  }

  async function loadWithdrawals() {
    try {
      setWithdrawalsLoading(true);

      const withdrawalService =
        new WithdrawalService();

      const data =
        await withdrawalService.getUserWithdrawals(
          userId
        );

      setWithdrawals(data);
    } catch (error) {
      console.error(
        "Failed to load withdrawals:",
        error
      );
    } finally {
      setWithdrawalsLoading(false);
    }
  }

  loadWithdrawals();
}, [currentUser?._id]);

  /**
   * ==========================================
   * LOADING WALLET
   * ==========================================
   */

  if (loading) {
    return (
      <Container>
        <section className="py-12">
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">
              Loading wallet...
            </p>
          </div>
        </section>
      </Container>
    );
  }

  return (
    <Container>
      <section className="py-12">

        {/* =========================
            HEADER
        ========================= */}

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">

          <div>
            <h1 className="text-4xl font-bold">
              My Wallet
            </h1>

            <p className="text-gray-500 mt-2">
              Manage your earnings and wallet transactions.
            </p>
          </div>

          <button
            onClick={refreshWallet}
            className="
              bg-blue-600
              hover:bg-blue-700
              text-white
              px-6
              py-3
              rounded-xl
              font-medium
            "
          >
            Refresh Wallet
          </button>

        </div>

        {/* =========================
            WALLET SUMMARY
        ========================= */}

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">

          {/* Balance */}

          <div className="bg-white shadow rounded-2xl p-6">

            <h2 className="text-gray-500">
              Available Balance
            </h2>

            <p className="text-3xl font-bold mt-3 text-blue-600">
              {balance.toLocaleString()}{currency}
            </p>

          </div>

          {/* Pending */}

          <div className="bg-white shadow rounded-2xl p-6">

            <h2 className="text-gray-500">
              Pending Balance
            </h2>

            <p className="text-3xl font-bold mt-3 text-yellow-600">
              {pendingBalance.toLocaleString()}{currency}
            </p>

          </div>

          {/* Total Earned */}

          <div className="bg-white shadow rounded-2xl p-6">

            <h2 className="text-gray-500">
              Total Earned
            </h2>

            <p className="text-3xl font-bold mt-3 text-green-600">
              {totalEarned.toLocaleString()} {currency}
            </p>

          </div>

          {/* Total Withdrawn */}

          <div className="bg-white shadow rounded-2xl p-6">

            <h2 className="text-gray-500">
              Total Withdrawn
            </h2>

            <p className="text-3xl font-bold mt-3 text-red-600">
              {totalWithdrawn.toLocaleString()} {currency}
            </p>

          </div>

        </div>

        {/* =========================
            WITHDRAWAL FORM
        ========================= */}

        <div className="mt-10">
          <WithdrawalForm />
        </div>

        {/* =========================
            WITHDRAWAL HISTORY
        ========================= */}

        <div className="bg-white rounded-2xl shadow mt-12 overflow-hidden">

          <div className="p-6 border-b">

            <h2 className="text-2xl font-bold">
              Withdrawal History
            </h2>

            <p className="text-gray-500 mt-1">
              Track your withdrawal requests.
            </p>

          </div>

          {withdrawalsLoading ? (

            <div className="text-center py-12 text-gray-500">
              Loading withdrawals...
            </div>

          ) : withdrawals.length === 0 ? (

            <div className="text-center py-12 text-gray-500">
              No withdrawals yet.
            </div>

          ) : (

            <div className="overflow-x-auto">

              <table className="w-full">

                <thead className="bg-gray-100">

                  <tr>

                    <th className="text-left p-4">
                      Amount
                    </th>

                    <th className="text-left p-4">
                      Fee
                    </th>

                    <th className="text-left p-4">
                      You Receive
                    </th>

                    <th className="text-left p-4">
                      Method
                    </th>

                    <th className="text-left p-4">
                      Status
                    </th>

                    <th className="text-left p-4">
                      Date
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {withdrawals.map(
                    (withdrawal) => (

                      <tr
                        key={
                          withdrawal._id
                        }
                        className="border-b last:border-b-0"
                      >

                        {/* Amount */}

                        <td className="p-4 font-semibold">

                          {withdrawal.requestedAmount.toFixed(
                            2
                          )}{" "}

                          {
                            withdrawal.currency
                          }

                        </td>

                        {/* Fee */}

                        <td className="p-4 text-red-600">

                          -
                          {withdrawal.feeAmount.toFixed(
                            2
                          )}{" "}

                          {
                            withdrawal.currency
                          }

                        </td>

                        {/* Net Amount */}

                        <td className="p-4 font-semibold text-green-600">

                          {withdrawal.netAmount.toFixed(
                            2
                          )}{" "}

                          {
                            withdrawal.currency
                          }

                        </td>

                        {/* Payment Method */}

                        <td className="p-4">

                          <div className="font-medium">

                            {withdrawal.paymentMethod.replace(
                              /_/g,
                              " "
                            )}

                          </div>

                          {withdrawal.network && (
                            <div className="text-sm text-gray-500">
                              {
                                withdrawal.network
                              }
                            </div>
                          )}

                        </td>

                        {/* Status */}

                        <td className="p-4">

                          <span
                            className={`
                              inline-flex
                              rounded-full
                              px-3
                              py-1
                              text-sm
                              font-medium
                              ${
                                withdrawal.status ===
                                "Completed"
                                  ? "bg-green-100 text-green-700"
                                  : withdrawal.status ===
                                    "Rejected"
                                  ? "bg-red-100 text-red-700"
                                  : withdrawal.status ===
                                    "Processing"
                                  ? "bg-blue-100 text-blue-700"
                                  : "bg-yellow-100 text-yellow-700"
                              }
                            `}
                          >
                            {
                              withdrawal.status
                            }
                          </span>

                        </td>

                        {/* Date */}

                        <td className="p-4 text-gray-500">

                          {new Date(
                            withdrawal.createdAt
                          ).toLocaleString()}

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

        {/* =========================
            WALLET TRANSACTION HISTORY
        ========================= */}

        <div className="bg-white rounded-2xl shadow mt-12 overflow-hidden">

          <div className="p-6 border-b">

            <h2 className="text-2xl font-bold">
              Transaction History
            </h2>

            <p className="text-gray-500 mt-1">
              Your latest wallet activity.
            </p>

          </div>

          {transactions.length === 0 ? (

            <div className="text-center py-16 text-gray-500">
              No wallet transactions yet.
            </div>

          ) : (

            <div className="overflow-x-auto">

              <table className="w-full">

                <thead className="bg-gray-100">

                  <tr>

                    <th className="text-left p-4">
                      Type
                    </th>

                    <th className="text-left p-4">
                      Description
                    </th>

                    <th className="text-left p-4">
                      Amount
                    </th>

                    <th className="text-left p-4">
                      Status
                    </th>

                    <th className="text-left p-4">
                      Date
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {transactions.map(
                    (transaction) => (

                      <tr
                        key={
                          transaction.id
                        }
                        className="border-b last:border-b-0"
                      >

                        <td className="p-4 font-medium">
                          {
                            transaction.type
                          }
                        </td>

                        <td className="p-4 text-gray-600">
                          {
                            transaction.description
                          }
                        </td>

                        <td className="p-4 font-semibold">

                          {transaction.amount.toLocaleString()}{" "}

                          {
                            transaction.currency
                          }

                        </td>

                        <td className="p-4">

                          <span
                            className={`
                              inline-flex
                              rounded-full
                              px-3
                              py-1
                              text-sm
                              font-medium
                              ${
                                transaction.status ===
                                "Completed"
                                  ? "bg-green-100 text-green-700"
                                  : transaction.status ===
                                    "Pending"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : "bg-red-100 text-red-700"
                              }
                            `}
                          >
                            {
                              transaction.status
                            }
                          </span>

                        </td>

                        <td className="p-4 text-gray-500">

                          {new Date(
                            transaction.date
                          ).toLocaleString()}

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </div>

      </section>
    </Container>
  );
}