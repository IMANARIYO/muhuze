import { useEffect, useState } from "react";

import Container from "../../components/ui/Container";
import { WithdrawalService } from "../../business/services/withdrawalService";
import type { Withdrawal } from "../../types/withdrawal";

export default function AdminWithdrawals() {
  const [withdrawals, setWithdrawals] =
    useState<Withdrawal[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [actionLoading, setActionLoading] =
    useState<string | null>(null);

  const withdrawalService =
    new WithdrawalService();

  /**
   * ==========================================
   * LOAD WITHDRAWALS
   * ==========================================
   */

  async function loadWithdrawals() {
    try {
      setLoading(true);
      setError("");

      const data =
        await withdrawalService.getAllWithdrawals();

      setWithdrawals(data);
    } catch (error) {
      console.error(
        "Failed to load withdrawals:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Failed to load withdrawals."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWithdrawals();
  }, []);

  /**
   * ==========================================
   * PROCESS
   * ==========================================
   *
   * Pending → Processing
   */

  async function handleProcess(
    withdrawalId: string
  ) {
    try {
      setActionLoading(withdrawalId);

      await withdrawalService.processWithdrawal(
        withdrawalId
      );

      await loadWithdrawals();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Failed to process withdrawal."
      );
    } finally {
      setActionLoading(null);
    }
  }

  /**
   * ==========================================
   * COMPLETE
   * ==========================================
   *
   * Processing → Completed
   */

  async function handleComplete(
    withdrawalId: string
  ) {
    try {
      setActionLoading(withdrawalId);

      await withdrawalService.completeWithdrawal(
        withdrawalId
      );

      await loadWithdrawals();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Failed to complete withdrawal."
      );
    } finally {
      setActionLoading(null);
    }
  }

  /**
   * ==========================================
   * REJECT
   * ==========================================
   *
   * Pending / Processing → Rejected
   */

  async function handleReject(
    withdrawalId: string
  ) {
    const reason = window.prompt(
      "Enter rejection reason:"
    );

    if (!reason?.trim()) {
      return;
    }

    try {
      setActionLoading(withdrawalId);

      await withdrawalService.rejectWithdrawal(
        withdrawalId,
        reason
      );

      await loadWithdrawals();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Failed to reject withdrawal."
      );
    } finally {
      setActionLoading(null);
    }
  }

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
              Loading withdrawals...
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
              Withdrawal Management
            </h1>

            <p className="text-gray-500 mt-2">
              Review and manage user withdrawal requests.
            </p>
          </div>

          <button
            onClick={loadWithdrawals}
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
            TABLE
        ========================================== */}

        <div className="bg-white rounded-2xl shadow overflow-hidden">

          <div className="p-6 border-b">
            <h2 className="text-2xl font-bold">
              All Withdrawals
            </h2>

            <p className="text-gray-500 mt-1">
              {withdrawals.length} withdrawal
              {withdrawals.length !== 1
                ? "s"
                : ""}
            </p>
          </div>

          {withdrawals.length === 0 ? (

            <div className="text-center py-16 text-gray-500">
              No withdrawals found.
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
                      Amount
                    </th>

                    <th className="text-left p-4">
                      Fee
                    </th>

                    <th className="text-left p-4">
                      Net
                    </th>

                    <th className="text-left p-4">
                      Method
                    </th>

                    <th className="text-left p-4">
                      Account
                    </th>

                    <th className="text-left p-4">
                      Status
                    </th>

                    <th className="text-left p-4">
                      Date
                    </th>

                    <th className="text-left p-4">
                      Action
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {withdrawals.map(
                    (withdrawal) => {

                      const busy =
                        actionLoading ===
                        withdrawal._id;

                      /**
                       * ==========================================
                       * GET USER INFORMATION
                       * ==========================================
                       *
                       * Backend now uses:
                       *
                       * .populate(
                       *   "userId",
                       *   "fullName email phone"
                       * )
                       *
                       * Therefore userId can be:
                       *
                       * string
                       *
                       * OR
                       *
                       * populated object.
                       */

                      const user =
                        typeof withdrawal.userId ===
                        "object"
                          ? withdrawal.userId
                          : null;

                      const userId =
                        typeof withdrawal.userId ===
                        "string"
                          ? withdrawal.userId
                          : withdrawal.userId._id;

                      return (
                        <tr
                          key={withdrawal._id}
                          className="border-b last:border-b-0"
                        >

                          {/* ==========================================
                              USER
                          ========================================== */}

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

                                {user.phone && (
                                  <p className="text-sm text-gray-500">
                                    {user.phone}
                                  </p>
                                )}

                              </div>
                            ) : (
                              <span className="text-sm">
                                {userId}
                              </span>
                            )}

                          </td>

                          {/* ==========================================
                              AMOUNT
                          ========================================== */}

                          <td className="p-4 font-semibold">
                            {withdrawal.requestedAmount.toFixed(
                              2
                            )}{" "}
                            {withdrawal.currency}
                          </td>

                          {/* ==========================================
                              FEE
                          ========================================== */}

                          <td className="p-4 text-red-600">
                            {withdrawal.feeAmount.toFixed(
                              2
                            )}{" "}
                            {withdrawal.currency}
                          </td>

                          {/* ==========================================
                              NET
                          ========================================== */}

                          <td className="p-4 font-semibold text-green-600">
                            {withdrawal.netAmount.toFixed(
                              2
                            )}{" "}
                            {withdrawal.currency}
                          </td>

                          {/* ==========================================
                              PAYMENT METHOD
                          ========================================== */}

                          <td className="p-4">

                            <div>

                              {withdrawal.paymentMethod}

                              {withdrawal.network && (
                                <p className="text-sm text-gray-500 mt-1">
                                  {withdrawal.network}
                                </p>
                              )}

                            </div>

                          </td>

                          {/* ==========================================
                              ACCOUNT
                          ========================================== */}

                          <td className="p-4">

                            <div>

                              <p>
                                {withdrawal.accountNumber}
                              </p>

                              {withdrawal.accountName && (
                                <p className="text-sm text-gray-500">
                                  {withdrawal.accountName}
                                </p>
                              )}

                            </div>

                          </td>

                          {/* ==========================================
                              STATUS
                          ========================================== */}

                          <td className="p-4">

                            <span
                              className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
                                withdrawal.status ===
                                "Completed"
                                  ? "bg-green-100 text-green-700"
                                  : withdrawal.status ===
                                    "Processing"
                                  ? "bg-blue-100 text-blue-700"
                                  : withdrawal.status ===
                                    "Pending"
                                  ? "bg-yellow-100 text-yellow-700"
                                  : withdrawal.status ===
                                    "Rejected"
                                  ? "bg-red-100 text-red-700"
                                  : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {withdrawal.status}
                            </span>

                          </td>

                          {/* ==========================================
                              DATE
                          ========================================== */}

                          <td className="p-4 text-gray-500 whitespace-nowrap">
                            {new Date(
                              withdrawal.createdAt
                            ).toLocaleString()}
                          </td>

                          {/* ==========================================
                              ACTION
                          ========================================== */}

                          <td className="p-4">

                            <div className="flex gap-2">

                              {/* PENDING */}

                              {withdrawal.status ===
                                "Pending" && (
                                <>
                                  <button
                                    disabled={busy}
                                    onClick={() =>
                                      handleProcess(
                                        withdrawal._id
                                      )
                                    }
                                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm"
                                  >
                                    {busy
                                      ? "..."
                                      : "Process"}
                                  </button>

                                  <button
                                    disabled={busy}
                                    onClick={() =>
                                      handleReject(
                                        withdrawal._id
                                      )
                                    }
                                    className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm"
                                  >
                                    Reject
                                  </button>
                                </>
                              )}

                              {/* PROCESSING */}

                              {withdrawal.status ===
                                "Processing" && (
                                <>
                                  <button
                                    disabled={busy}
                                    onClick={() =>
                                      handleComplete(
                                        withdrawal._id
                                      )
                                    }
                                    className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm"
                                  >
                                    {busy
                                      ? "..."
                                      : "Complete"}
                                  </button>

                                  <button
                                    disabled={busy}
                                    onClick={() =>
                                      handleReject(
                                        withdrawal._id
                                      )
                                    }
                                    className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white px-3 py-2 rounded-lg text-sm"
                                  >
                                    Reject
                                  </button>
                                </>
                              )}

                              {/* COMPLETED */}

                              {withdrawal.status ===
                                "Completed" && (
                                <span className="text-green-600 text-sm font-medium">
                                  Completed
                                </span>
                              )}

                              {/* REJECTED */}

                              {withdrawal.status ===
                                "Rejected" && (
                                <span className="text-red-600 text-sm font-medium">
                                  Rejected
                                </span>
                              )}

                            </div>

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