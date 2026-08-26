import { useEffect, useState } from "react";

import Container from "../../components/ui/Container";

import {
  walletTransactionService,
} from "../../business/services/walletTransactionService";

import type {
  WalletTransaction,
} from "../../types/walletTransaction";

export default function WalletTransactions() {
  const [
    transactions,
    setTransactions,
  ] = useState<WalletTransaction[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  /**
   * ==========================================
   * LOAD TRANSACTIONS
   * ==========================================
   */

  async function loadTransactions() {
    try {
      setLoading(true);
      setError("");

      const data =
        await walletTransactionService.getAllTransactions();

      setTransactions(data);
    } catch (error) {
      console.error(
        "Failed to load transactions:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Failed to load transactions."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, []);

  /**
   * ==========================================
   * LOADING
   * ==========================================
   */

  if (loading) {
    return (
      <Container>
        <section className="py-12">
          <div className="text-center py-20">
            <p className="text-gray-500 text-lg">
              Loading wallet transactions...
            </p>
          </div>
        </section>
      </Container>
    );
  }

  return (
    <Container>
      <section className="py-12">

        {/* ==========================================
            HEADER
        ========================================== */}

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">

          <div>
            <h1 className="text-4xl font-bold">
              Wallet Transactions
            </h1>

            <p className="text-gray-500 mt-2">
              View all wallet financial activity.
            </p>
          </div>

          <button
            onClick={loadTransactions}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-medium"
          >
            Refresh
          </button>

        </div>

        {/* ==========================================
            ERROR
        ========================================== */}

        {error && (
          <div className="mb-6 bg-red-100 text-red-700 rounded-xl p-4">
            {error}
          </div>
        )}

        {/* ==========================================
            TRANSACTIONS
        ========================================== */}

        <div className="bg-white rounded-2xl shadow overflow-hidden">

          <div className="p-6 border-b">

            <h2 className="text-2xl font-bold">
              All Transactions
            </h2>

            <p className="text-gray-500 mt-1">
              {transactions.length} transaction
              {transactions.length !== 1
                ? "s"
                : ""}
            </p>

          </div>

          {transactions.length === 0 ? (

            <div className="text-center py-16 text-gray-500">
              No wallet transactions found.
            </div>

          ) : (

            <div className="overflow-x-auto">

              <table className="w-full">

                <thead className="bg-gray-100">

                  <tr>

                    <th className="text-left p-4">
                      User
                    </th>

                    <th className="text-left p-4">
                      Type
                    </th>

                    <th className="text-left p-4">
                      Amount
                    </th>

                    <th className="text-left p-4">
                      Currency
                    </th>

                    <th className="text-left p-4">
                      Status
                    </th>

                    <th className="text-left p-4">
                      Description
                    </th>

                    <th className="text-left p-4">
                      Date
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {transactions.map(
                    (transaction) => {

                      const user =
                        typeof transaction.userId ===
                        "object"
                          ? transaction.userId
                          : null;

                      const userId =
                        typeof transaction.userId ===
                        "string"
                          ? transaction.userId
                          : transaction.userId._id;

                      const isPositive =
                        transaction.amount >= 0;

                      return (
                        <tr
                          key={transaction._id}
                          className="border-b last:border-b-0"
                        >

                          {/* USER */}

                          <td className="p-4">

                            {user ? (
                              <div>

                                <p className="font-medium">
                                  {user.fullName}
                                </p>

                                {user.email && (
                                  <p className="text-sm text-gray-500">
                                    {user.email}
                                  </p>
                                )}

                              </div>
                            ) : (
                              <span className="text-sm">
                                {userId}
                              </span>
                            )}

                          </td>

                          {/* TYPE */}

                          <td className="p-4">

                            <span className="font-medium">
                              {transaction.type}
                            </span>

                          </td>

                          {/* AMOUNT */}

                          <td
                            className={`p-4 font-semibold ${
                              isPositive
                                ? "text-green-600"
                                : "text-red-600"
                            }`}
                          >
                            {isPositive
                              ? "+"
                              : ""}
                            {transaction.amount.toFixed(
                              2
                            )}
                          </td>

                          {/* CURRENCY */}

                          <td className="p-4">
                            {transaction.currency}
                          </td>

                          {/* STATUS */}

                          <td className="p-4">

                            <span
                              className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
                                transaction.status ===
                                "Completed"
                                  ? "bg-green-100 text-green-700"
                                  : transaction.status ===
                                    "Pending"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : transaction.status ===
                                    "Cancelled"
                                  ? "bg-gray-100 text-gray-700"
                                  : "bg-red-100 text-red-700"
                              }`}
                            >
                              {transaction.status}
                            </span>

                          </td>

                          {/* DESCRIPTION */}

                          <td className="p-4 text-gray-600 max-w-xs">
                            {transaction.description ||
                              "-"}
                          </td>

                          {/* DATE */}

                          <td className="p-4 text-gray-500 whitespace-nowrap">
                            {new Date(
                              transaction.createdAt
                            ).toLocaleString()}
                          </td>

                        </tr>
                      );
                    }
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