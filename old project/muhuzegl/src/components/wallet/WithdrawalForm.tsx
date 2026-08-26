import { useMemo, useState } from "react";

import { useWallet } from "../../context/WalletContext";

import { useToast } from "../ui/Toast";
import { apiClient } from "../../business/services/apiClient";


/**
 * ==========================================
 * PAYMENT METHODS
 * ==========================================
 */

type PaymentMethod =
  | "MTN_MOBILE_MONEY"
  | "AIRTEL_MONEY"
  | "BANK_TRANSFER"
  | "USDT"
  | "USDC";

/**
 * ==========================================
 * CRYPTO NETWORKS
 * ==========================================
 */

type CryptoNetwork =
  | "TRC20"
  | "ERC20"
  | "BEP20"
  | "POLYGON"
  | "ARBITRUM"
  | "SOLANA";

/**
 * ==========================================
 * WITHDRAWAL FORM
 * ==========================================
 */

export default function WithdrawalForm() {

  /**
   * ==========================================
   * WALLET
   * ==========================================
   */

  const {
    balance,
    refreshWallet,
  } = useWallet();

  /**
   * ==========================================
   * TOAST
   * ==========================================
   */

  const { showToast } =
    useToast();

  /**
   * ==========================================
   * FORM STATE
   * ==========================================
   */

  const [amount, setAmount] =
    useState("");

  const [paymentMethod, setPaymentMethod] =
    useState<PaymentMethod>(
      "MTN_MOBILE_MONEY"
    );

  const [network, setNetwork] =
    useState<CryptoNetwork>(
      "TRC20"
    );

  const [accountNumber, setAccountNumber] =
    useState("");

  const [accountName, setAccountName] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  /**
   * ==========================================
   * CRYPTO PAYMENT?
   * ==========================================
   */

  const isCrypto =
    paymentMethod === "USDT" ||
    paymentMethod === "USDC";

  /**
   * ==========================================
   * CALCULATE WITHDRAWAL AMOUNT
   * ==========================================
   *
   * MUHUZE withdrawal fee:
   *
   * 5%
   *
   * Example:
   *
   * Withdrawal = $100
   * Fee        = $5
   * Receive    = $95
   *
   * Backend remains the final authority.
   */

  const withdrawalAmount =
    Number(amount) || 0;

  /**
   * ==========================================
   * FEE
   * ==========================================
   */

  const feeAmount = useMemo(() => {
    return Number(
      (
        withdrawalAmount * 0.05
      ).toFixed(2)
    );
  }, [withdrawalAmount]);

  /**
   * ==========================================
   * NET AMOUNT
   * ==========================================
   */

  const netAmount = useMemo(() => {
    return Number(
      (
        withdrawalAmount -
        feeAmount
      ).toFixed(2)
    );
  }, [
    withdrawalAmount,
    feeAmount,
  ]);

  /**
   * ==========================================
   * ACCOUNT LABEL
   * ==========================================
   */

  const accountLabel =
    isCrypto
      ? "Wallet Address"
      : paymentMethod ===
        "BANK_TRANSFER"
      ? "Bank Account Number"
      : "Phone Number";

  /**
   * ==========================================
   * SUBMIT WITHDRAWAL
   * ==========================================
   */

  async function handleSubmit(
    e: React.FormEvent<HTMLFormElement>
  ) {

    e.preventDefault();

    /**
     * ========================================
     * MINIMUM WITHDRAWAL
     * ========================================
     *
     * MUHUZE rule:
     *
     * Minimum withdrawal = $5
     */

    if (
      withdrawalAmount < 5
    ) {
      showToast(
        "Minimum withdrawal amount is $5.",
        "warning"
      );

      return;
    }

    /**
     * ========================================
     * BALANCE CHECK
     * ========================================
     */

    if (
      withdrawalAmount >
      balance
    ) {
      showToast(
        "Insufficient wallet balance.",
        "error"
      );

      return;
    }

    /**
     * ========================================
     * ACCOUNT NUMBER / WALLET ADDRESS
     * ========================================
     */

    if (
      !accountNumber.trim()
    ) {
      showToast(
        `${accountLabel} is required.`,
        "warning"
      );

      return;
    }

    /**
     * ========================================
     * ACCOUNT NAME
     * ========================================
     */

    if (
      !accountName.trim()
    ) {
      showToast(
        "Account name is required.",
        "warning"
      );

      return;
    }

    /**
     * ========================================
     * CRYPTO NETWORK
     * ========================================
     */

    if (
      isCrypto &&
      !network
    ) {
      showToast(
        "Please select a crypto network.",
        "warning"
      );

      return;
    }

    try {

      setLoading(true);

      /**
       * ======================================
       * CREATE WITHDRAWAL
       * ======================================
       *
       * IMPORTANT:
       *
       * We do NOT send userId here.
       *
       * apiClient automatically sends:
       *
       * Authorization:
       * Bearer <JWT>
       *
       * The backend gets the user from:
       *
       * req.user._id
       */

      const result =
        await apiClient.post<{
          success: boolean;

          message: string;

          data: unknown;
        }>(
          "/withdrawals",
          {
            amount:
              withdrawalAmount,

            paymentMethod,

            network:
              isCrypto
                ? network
                : undefined,

            accountNumber:
              accountNumber.trim(),

            accountName:
              accountName.trim(),
          }
        );

      /**
       * ======================================
       * CHECK BACKEND RESPONSE
       * ======================================
       */

      if (
        !result.success
      ) {
        throw new Error(
          result.message ||
            "Withdrawal request failed."
        );
      }

      /**
       * ======================================
       * SUCCESS MESSAGE
       * ======================================
       */

      showToast(
        "Withdrawal request submitted successfully!",
        "success"
      );

      /**
       * ======================================
       * CLEAR FORM
       * ======================================
       */

      setAmount("");

      setAccountNumber("");

      setAccountName("");

      /**
       * ======================================
       * REFRESH WALLET
       * ======================================
       */

      await refreshWallet();

    } catch (error) {

      console.error(
        "WITHDRAWAL ERROR:",
        error
      );

      showToast(
        error instanceof Error
          ? error.message
          : "Unable to create withdrawal request.",
        "error"
      );

    } finally {

      setLoading(false);
    }
  }

  /**
   * ==========================================
   * UI
   * ==========================================
   */

  return (
    <div className="bg-white rounded-3xl shadow-lg p-8 mt-10">

      {/* =====================================
          HEADER
      ====================================== */}

      <div className="mb-8">

        <h2 className="text-2xl font-bold">
          Withdraw Funds
        </h2>

        <p className="text-gray-500 mt-2">

          Available balance:{" "}

          <span className="font-semibold text-blue-600">

            {balance.toLocaleString()} USD

          </span>

        </p>

      </div>

      {/* =====================================
          FORM
      ====================================== */}

      <form
        onSubmit={handleSubmit}
        className="space-y-6"
      >

        {/* ==================================
            AMOUNT
        ================================== */}

        <div>

          <label
            className="block mb-2 font-medium text-gray-700"
          >
            Withdrawal Amount
          </label>

          <input
            type="number"
            min="5"
            step="0.01"
            value={amount}
            onChange={(e) =>
              setAmount(
                e.target.value
              )
            }
            placeholder="Enter amount"
            className="
              w-full
              rounded-xl
              border
              border-gray-300
              px-4
              py-3
              outline-none
              focus:ring-2
              focus:ring-blue-500
            "
          />

          <p className="text-sm text-gray-500 mt-2">
            Minimum withdrawal: $5
          </p>

        </div>

        {/* ==================================
            PAYMENT METHOD
        ================================== */}

        <div>

          <label
            className="block mb-2 font-medium text-gray-700"
          >
            Payment Method
          </label>

          <select
            value={paymentMethod}
            onChange={(e) =>
              setPaymentMethod(
                e.target
                  .value as PaymentMethod
              )
            }
            className="
              w-full
              rounded-xl
              border
              border-gray-300
              px-4
              py-3
              outline-none
              focus:ring-2
              focus:ring-blue-500
            "
          >

            <option value="MTN_MOBILE_MONEY">
              MTN Mobile Money
            </option>

            <option value="AIRTEL_MONEY">
              Airtel Money
            </option>

            <option value="BANK_TRANSFER">
              Bank Transfer
            </option>

            <option value="USDT">
              USDT
            </option>

            <option value="USDC">
              USDC
            </option>

          </select>

        </div>

        {/* ==================================
            CRYPTO NETWORK
        ================================== */}

        {isCrypto && (

          <div>

            <label
              className="block mb-2 font-medium text-gray-700"
            >
              Network
            </label>

            <select
              value={network}
              onChange={(e) =>
                setNetwork(
                  e.target
                    .value as CryptoNetwork
                )
              }
              className="
                w-full
                rounded-xl
                border
                border-gray-300
                px-4
                py-3
                outline-none
                focus:ring-2
                focus:ring-blue-500
              "
            >

              <option value="TRC20">
                TRC20
              </option>

              <option value="ERC20">
                ERC20
              </option>

              <option value="BEP20">
                BEP20
              </option>

              <option value="POLYGON">
                Polygon
              </option>

              <option value="ARBITRUM">
                Arbitrum
              </option>

              <option value="SOLANA">
                Solana
              </option>

            </select>

            <p className="text-sm text-gray-500 mt-2">
              Make sure the selected network
              matches your wallet address.
            </p>

          </div>
        )}

        {/* ==================================
            ACCOUNT / WALLET
        ================================== */}

        <div>

          <label
            className="block mb-2 font-medium text-gray-700"
          >
            {accountLabel}
          </label>

          <input
            type="text"
            value={accountNumber}
            onChange={(e) =>
              setAccountNumber(
                e.target.value
              )
            }
            placeholder={
              isCrypto
                ? "Enter wallet address"
                : "Enter account or phone number"
            }
            className="
              w-full
              rounded-xl
              border
              border-gray-300
              px-4
              py-3
              outline-none
              focus:ring-2
              focus:ring-blue-500
            "
          />

        </div>

        {/* ==================================
            ACCOUNT NAME
        ================================== */}

        <div>

          <label
            className="block mb-2 font-medium text-gray-700"
          >
            Account Name
          </label>

          <input
            type="text"
            value={accountName}
            onChange={(e) =>
              setAccountName(
                e.target.value
              )
            }
            placeholder="Enter account holder name"
            className="
              w-full
              rounded-xl
              border
              border-gray-300
              px-4
              py-3
              outline-none
              focus:ring-2
              focus:ring-blue-500
            "
          />

        </div>

        {/* ==================================
            FEE SUMMARY
        ================================== */}

        {withdrawalAmount > 0 && (

          <div className="bg-gray-50 rounded-2xl p-5 space-y-3">

            <div className="flex justify-between">

              <span className="text-gray-600">
                Withdrawal amount
              </span>

              <span className="font-semibold">
                {withdrawalAmount.toFixed(2)} USD
              </span>

            </div>

            <div className="flex justify-between">

              <span className="text-gray-600">
                Withdrawal fee (5%)
              </span>

              <span className="font-semibold text-red-600">
                -{feeAmount.toFixed(2)} USD
              </span>

            </div>

            <div className="border-t pt-3 flex justify-between">

              <span className="font-semibold">
                You receive
              </span>

              <span className="font-bold text-green-600">
                {netAmount.toFixed(2)} USD
              </span>

            </div>

          </div>
        )}

        {/* ==================================
            WITHDRAWAL RULES
        ================================== */}

        <div className="bg-blue-50 rounded-2xl p-5">

          <h3 className="font-semibold text-blue-900 mb-3">
            Withdrawal Rules
          </h3>

          <ul className="text-sm text-blue-800 space-y-1">

            <li>
              • Minimum withdrawal: $5
            </li>

            <li>
              • Withdrawal fee: 5%
            </li>

            <li>
              • Withdrawals are available once per week
            </li>

            <li>
              • Only available balance can be withdrawn
            </li>

            <li>
              • Pending balance cannot be withdrawn
            </li>

          </ul>

        </div>

        {/* ==================================
            SUBMIT
        ================================== */}

        <button
          type="submit"
          disabled={
            loading ||
            withdrawalAmount < 5 ||
            withdrawalAmount >
              balance
          }
          className="
            w-full
            bg-blue-600
            hover:bg-blue-700
            disabled:bg-gray-400
            text-white
            rounded-xl
            py-4
            font-semibold
            transition
          "
        >

          {loading
            ? "Submitting..."
            : "Request Withdrawal"}

        </button>

      </form>

    </div>
  );
}