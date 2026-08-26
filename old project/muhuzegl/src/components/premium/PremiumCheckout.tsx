import { useState } from "react";
import type { PremiumPlan } from "../../types/premium";

interface PremiumCheckoutProps {
  open: boolean;
  plan: PremiumPlan | null;
  onClose: () => void;
  onConfirm: (
    cryptoCurrency: "USDT" | "USDC",
    cryptoNetwork: "BEP20" | "ERC20"
  ) => void;
}

export default function PremiumCheckout({
  open,
  plan,
  onClose,
  onConfirm,
}: PremiumCheckoutProps) {
  const [cryptoCurrency, setCryptoCurrency] =
    useState<"USDT" | "USDC">("USDT");

  const [cryptoNetwork, setCryptoNetwork] =
    useState<"BEP20" | "ERC20">("BEP20");

  if (!open || !plan) {
    return null;
  }

  const handleConfirm = () => {
    onConfirm(
      cryptoCurrency,
      cryptoNetwork
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-50 p-5">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">

        {/* ==========================================
            HEADER
        ========================================== */}

        <div className="border-b p-6">

          <h2 className="text-3xl font-bold">
            Premium Checkout
          </h2>

          <p className="text-gray-500 mt-2">
            Complete your Premium membership purchase.
          </p>

        </div>

        {/* ==========================================
            PLAN
        ========================================== */}

        <div className="p-6">

          <div className="bg-blue-50 rounded-xl p-5 mb-6">

            <h3 className="text-2xl font-bold">
              {plan.name}
            </h3>

            <p className="text-blue-700 text-4xl font-bold mt-3">
              ${plan.price.toLocaleString()} USD
            </p>

            <p className="text-gray-500 mt-2">
              {plan.duration} Days Membership
            </p>

          </div>

          {/* ==========================================
              PAYMENT METHOD
          ========================================== */}

          <h4 className="font-bold text-lg mb-4">
            Select Payment Method
          </h4>

          <div className="border rounded-xl p-5 bg-gray-50">

            <div className="flex items-center gap-3 mb-5">

              <input
                type="radio"
                name="paymentMethod"
                value="CRYPTO"
                checked
                readOnly
              />

              <div>
                <p className="font-semibold">
                  Cryptocurrency
                </p>

                <p className="text-sm text-gray-500">
                  Secure payment through NOWPayments
                </p>
              </div>

            </div>

            {/* ========================================
                CRYPTO CURRENCY
            ======================================== */}

            <label className="block font-semibold mb-2">
              Cryptocurrency
            </label>

            <select
              value={cryptoCurrency}
              onChange={(event) =>
                setCryptoCurrency(
                  event.target.value as
                    | "USDT"
                    | "USDC"
                )
              }
className="w-full border rounded-xl px-4 py-3 mb-5 focus:outline-none focus:ring-2 focus:ring-blue-500"            >
              <option value="USDT">
                USDT
              </option>

              <option value="USDC">
                USDC
              </option>
            </select>

            {/* ========================================
                NETWORK
            ======================================== */}

            <label className="block font-semibold mb-2">
              Network
            </label>

            <select
              value={cryptoNetwork}
              onChange={(event) =>
                setCryptoNetwork(
                  event.target.value as
                    | "BEP20"
                    | "ERC20"
                )
              }
              className="w-full border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="BEP20">
                BEP20
              </option>

              <option value="ERC20">
                ERC20
              </option>
            </select>

          </div>

          {/* ==========================================
              PAYMENT INFORMATION
          ========================================== */}

          <div className="mt-5 rounded-xl border border-yellow-200 bg-yellow-50 p-4">

            <p className="text-sm text-yellow-800">

              Your Premium membership will remain
              <strong> Pending </strong>
              until Muhuze Global Ink confirms your payment.

            </p>

          </div>

        </div>

        {/* ==========================================
            FOOTER
        ========================================== */}

        <div className="border-t p-6 flex justify-end gap-4">

          <button
            type="button"
            onClick={onClose}
            className="px-6 py-3 rounded-xl border hover:bg-gray-100"
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={handleConfirm}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl"
          >
            Continue to Payment
          </button>

        </div>

      </div>

    </div>
  );
}