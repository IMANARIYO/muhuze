import { useState } from "react";
import { QRCodeSVG } from "qrcode.react";

import type { PremiumPlan } from "../../types/premium";
import type { PremiumPaymentResult } from "../../business/services/premiumApiService";

interface PremiumSuccessProps {
  open: boolean;
  plan: PremiumPlan | null;
  payment: PremiumPaymentResult | null;
  onClose: () => void;
  onCheckStatus?: () => void;
  onCancelPayment?: () => void;
  checkingStatus?: boolean;
  cancellingPayment?: boolean;
}

export default function PremiumSuccess({
  open,
  plan,
  payment,
  onClose,
  onCheckStatus,
  onCancelPayment,
  checkingStatus = false,
  cancellingPayment = false,
}: PremiumSuccessProps) {
  const [copied, setCopied] = useState(false);

  if (!open || !plan || !payment) {
    return null;
  }

  const payAddress =
    payment.provider.payAddress ||
    payment.payment.walletAddress ||
    "";

  const payAmount =
    payment.provider.payAmount ??
    payment.payment.cryptoAmount ??
    0;

  const payCurrency =
    payment.provider.payCurrency ||
    payment.payment.cryptoCurrency;

  const paymentStatus =
    payment.provider.paymentStatus ||
    payment.payment.status;

  const network =
    payment.payment.cryptoNetwork;

  const copyAddress = async () => {
    if (!payAddress) {
      return;
    }

    try {
      await navigator.clipboard.writeText(
        payAddress
      );

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (error) {
      console.error(
        "Failed to copy payment address:",
        error
      );
    }
  };

  /**
   * ==========================================
   * QR VALUE
   * ==========================================
   *
   * For now we encode the payment address.
   *
   * We deliberately do NOT expose the
   * NOWPayments payment ID.
   */

  const qrValue = payAddress;

  return (
    <div className="fixed inset-0 bg-black/70 flex justify-center items-center z-50 p-4">

      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[92vh] overflow-y-auto">

        {/* ======================================
            HEADER
        ====================================== */}

        <div className="border-b p-6">

          <div className="flex justify-between items-start gap-4">

            <div>
              <h1 className="text-2xl md:text-3xl font-bold">
                Premium Payment
              </h1>

              <p className="text-gray-500 mt-2">
                Complete your payment using the
                information below.
              </p>
            </div>

            <span className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 text-sm font-semibold">
              Pending
            </span>

          </div>

        </div>

        {/* ======================================
            PAYMENT CONTENT
        ====================================== */}

        <div className="p-6 space-y-6">

          {/* ====================================
              QR CODE
          ==================================== */}

          <div className="flex flex-col items-center">

            <div className="bg-white border rounded-2xl p-5 shadow-sm">

              {qrValue ? (
                <QRCodeSVG
                  value={qrValue}
                  size={220}
                  level="M"
                  marginSize={4}
                />
              ) : (
                <div className="w-[220px] h-[220px] flex items-center justify-center bg-gray-100 rounded-xl">
                  <p className="text-gray-500 text-sm text-center">
                    Payment address
                    unavailable
                  </p>
                </div>
              )}

            </div>

            <p className="text-sm text-gray-500 mt-4 text-center">
              Scan this QR code with your crypto
              wallet.
            </p>

          </div>

          {/* ====================================
              PAYMENT AMOUNT
          ==================================== */}

          <div className="rounded-2xl bg-blue-50 border border-blue-100 p-5">

            <p className="text-sm text-blue-700 font-medium">
              Amount to Pay
            </p>

            <p className="text-3xl md:text-4xl font-bold text-blue-900 mt-1 break-all">

              {payAmount
                ? Number(payAmount).toLocaleString(
                    undefined,
                    {
                      maximumFractionDigits: 12,
                    }
                  )
                : "—"}

              {" "}

              {payCurrency}

            </p>

          </div>

          {/* ====================================
              PAYMENT DETAILS
          ==================================== */}

          <div className="border rounded-2xl overflow-hidden">

            <div className="px-5 py-4 border-b bg-gray-50">

              <h2 className="font-bold text-lg">
                Payment Details
              </h2>

            </div>

            <div className="p-5 space-y-5">

              {/* Membership */}

              <div className="flex justify-between gap-4">

                <span className="text-gray-500">
                  Membership
                </span>

                <strong className="text-right">
                  {plan.name}
                </strong>

              </div>

              {/* Network */}

              <div className="flex justify-between gap-4">

                <span className="text-gray-500">
                  Network
                </span>

                <strong>
                  {network}
                </strong>

              </div>

              {/* Status */}

              <div className="flex justify-between gap-4">

                <span className="text-gray-500">
                  Status
                </span>

                <strong className="text-yellow-600">
                  {paymentStatus}
                </strong>

              </div>

              {/* Address */}

              <div>

                <p className="text-gray-500 mb-2">
                  Payment Address
                </p>

                <div className="bg-gray-100 rounded-xl p-4">

                  <p className="font-mono text-sm break-all">
                    {payAddress || "Unavailable"}
                  </p>

                </div>

                <button
                  type="button"
                  onClick={copyAddress}
                  disabled={!payAddress}
                  className="mt-3 w-full border border-blue-600 text-blue-600 hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl py-3 font-semibold transition"
                >
                  {copied
                    ? "Address Copied ✓"
                    : "Copy Payment Address"}
                </button>

              </div>

            </div>

          </div>

          {/* ====================================
              WARNING
          ==================================== */}

          <div className="rounded-2xl border border-yellow-200 bg-yellow-50 p-5">

            <p className="font-semibold text-yellow-900">
              Important
            </p>

            <p className="text-sm text-yellow-800 mt-2">
              Send the displayed amount using
              the selected network.
            </p>

            <p className="text-sm text-yellow-800 mt-2">
              Sending through another network
              may result in loss of funds.
            </p>

            <p className="text-sm text-yellow-800 mt-2">
              Your Premium membership remains
              pending until the payment is
              confirmed.
            </p>

          </div>

          {/* ====================================
              ACTIONS
          ==================================== */}

          <div className="space-y-3">

            {onCheckStatus && (
              <button
                type="button"
                onClick={onCheckStatus}
                disabled={
                  checkingStatus ||
                  cancellingPayment
                }
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-xl py-3 font-semibold transition"
              >
                {checkingStatus
                  ? "Checking Payment..."
                  : "Check Payment Status"}
              </button>
            )}

            {onCancelPayment && (
              <button
                type="button"
                onClick={onCancelPayment}
                disabled={
                  checkingStatus ||
                  cancellingPayment
                }
                className="w-full border border-red-500 text-red-600 hover:bg-red-50 disabled:opacity-50 rounded-xl py-3 font-semibold transition"
              >
                {cancellingPayment
                  ? "Cancelling..."
                  : "Cancel Pending Payment"}
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              disabled={
                checkingStatus ||
                cancellingPayment
              }
              className="w-full border rounded-xl py-3 hover:bg-gray-100 disabled:opacity-50 font-semibold transition"
            >
              Close
            </button>

          </div>

        </div>

      </div>

    </div>
  );
}