import {
  useEffect,
  useState,
} from "react";

import Container from "../../components/ui/Container";

import {
  PremiumHero,
  PremiumCard,
  PremiumComparison,
  PremiumFAQ,
  PremiumStatus,
  PremiumAnalytics,
  PremiumReminder,
  PremiumHistory,
  PremiumCheckout,
  PremiumSuccess,
} from "../../components/premium";

import { PREMIUM_PLANS } from "../../business/premiumPlans";

import {
  premiumApiService,
  type PremiumPaymentResult,
  type PremiumSubscriptionResponse,
} from "../../business/services/premiumApiService";

import { usePremium } from "../../context/PremiumContext";
import { useAuth } from "../../context/AuthContext";

import type { PremiumPlan } from "../../types/premium";

export default function Premium() {
  const {
    subscription,
    daysRemaining,
  } = usePremium();

  const { currentUser } = useAuth();

  /**
   * ==========================================
   * PLAN / CHECKOUT STATE
   * ==========================================
   */

  const [selectedPlan, setSelectedPlan] =
    useState<PremiumPlan | null>(null);

  const [checkoutOpen, setCheckoutOpen] =
    useState(false);

  const [successOpen, setSuccessOpen] =
    useState(false);

  /**
   * ==========================================
   * PAYMENT STATE
   * ==========================================
   */

  const [loading, setLoading] =
    useState(false);

  const [paymentData, setPaymentData] =
    useState<PremiumPaymentResult | null>(
      null
    );

  /**
   * ==========================================
   * BACKEND PREMIUM STATE
   * ==========================================
   *
   * This is the real Premium state from
   * the MUHUZE backend.
   *
   * It is intentionally separate from
   * PremiumContext because PremiumContext
   * currently uses localStorage.
   */

  const [
    backendSubscription,
    setBackendSubscription,
  ] =
    useState<PremiumSubscriptionResponse | null>(
      null
    );

  const [
    cancelLoading,
    setCancelLoading,
  ] = useState(false);

  const [checkLoading, setCheckLoading] =
  useState(false);

  /**
   * ==========================================
   * AUTHENTICATION
   * ==========================================
   */

 useEffect(() => {
  async function loadPremiumStatus() {
    if (!currentUser) {
      return;
    }

    try {
      const result =
        await premiumApiService.getMyPremium();

      if (result.success) {
        setBackendSubscription(result.data);
      }
    } catch (error) {
      console.error(
        "Unable to load Premium status:",
        error
      );
    }
  }

  loadPremiumStatus();
}, [currentUser]);

if (!currentUser) {
  return null;
}

const userId = currentUser._id;
  /**
   * ==========================================
   * SELECT PREMIUM PLAN
   * ==========================================
   */

  function handleSelectPlan(
    plan: PremiumPlan
  ) {
    /**
     * Do not allow another Premium payment
     * while one is already pending.
     */

    if (
      backendSubscription?.status ===
      "Pending"
    ) {
      alert(
        "You already have a pending Premium payment. Please complete or cancel it first."
      );

      return;
    }

    /**
     * Do not allow another purchase while
     * Premium is active.
     */

    if (
      backendSubscription?.status ===
      "Active"
    ) {
      alert(
        "You already have an active Premium membership."
      );

      return;
    }

    setSelectedPlan(plan);

    setCheckoutOpen(true);
  }

  /**
   * ==========================================
   * CONFIRM PREMIUM PAYMENT
   * ==========================================
   *
   * Flow:
   *
   * Frontend
   *    ↓
   * POST /api/premium
   *    ↓
   * Pending Subscription
   *    ↓
   * Pending Payment
   *    ↓
   * NOWPayments
   *    ↓
   * Customer pays
   *    ↓
   * NOWPayments IPN
   *    ↓
   * Backend confirms payment
   *    ↓
   * Premium activated
   *
   * IMPORTANT:
   *
   * Premium is NOT activated here.
   */
async function handleConfirmPayment(
  cryptoCurrency: "USDT" | "USDC",
  cryptoNetwork: "BEP20" | "ERC20"
) {
  if (!selectedPlan) {
    return;
  }

  try {
    setLoading(true);

    /**
     * ==========================================
     * FIRST CHECK EXISTING PREMIUM
     * ==========================================
     *
     * If a Pending subscription already exists,
     * resume that payment instead of creating
     * another one.
     */

    const currentPremium =
      await premiumApiService.getMyPremium();

    const existingSubscription =
      currentPremium.data;

    if (
      existingSubscription &&
      existingSubscription.status === "Pending"
    ) {
      /**
       * Existing payment
       */
      const existingPayment =
        existingSubscription.paymentId;

      /**
       * Make sure the payment is populated.
       */
      if (
        existingPayment &&
        typeof existingPayment !== "string"
      ) {
        /**
         * Reconstruct the PremiumPaymentResult
         * expected by PremiumSuccess.
         */

        setPaymentData({
          payment: existingPayment,

          provider: {
            paymentId:
              existingPayment.providerPaymentId ||
              "",

            payAddress:
              existingPayment.walletAddress,

            payAmount:
              existingPayment.cryptoAmount,

            payCurrency:
              existingPayment.cryptoCurrency,

            paymentStatus:
              existingPayment.status,

            expirationEstimate:
              undefined,
          },
        });

        setCheckoutOpen(false);
        setSuccessOpen(true);

        return;
      }

      /**
       * Existing subscription exists but
       * payment information is unavailable.
       */
      alert(
        "Your Premium payment is already pending, but its payment information could not be loaded."
      );

      return;
    }

    /**
     * ==========================================
     * NO PENDING PAYMENT
     * ==========================================
     *
     * Only now create a new payment.
     */

    const result =
      await premiumApiService.createPremiumPayment({
        plan: selectedPlan.name,
        cryptoCurrency,
        cryptoNetwork,
      });

    if (!result.success) {
      alert(
        result.message ||
          "Premium payment could not be created."
      );

      return;
    }

    /**
     * Save NEW payment information.
     */

    setPaymentData(
      result.data.payment
    );

    setCheckoutOpen(false);
    setSuccessOpen(true);

  } catch (error) {
    console.error(
      "Premium payment error:",
      error
    );

    alert(
      error instanceof Error
        ? error.message
        : "Unable to create Premium payment."
    );
  } finally {
    setLoading(false);
  }
}
/**
 * ==========================================
 * CHECK PAYMENT STATUS
 * ==========================================
 */

async function handleCheckStatus() {
  if (!paymentData) {
    return;
  }

  try {
    setCheckLoading(true);

    console.log(
      "🔎 Checking payment status..."
    );

    const result =
      await premiumApiService.checkPaymentStatus(
        paymentData.payment._id
      );

    console.log(
      "🔎 Payment status result:",
      result
    );

    if (!result.success) {
      alert(
        result.message ||
          "Unable to check payment status."
      );

      return;
    }

    // Update payment information
    setPaymentData(
      result.data
    );

    const status =
      result.data.payment.status;

    // ========================================
    // PAYMENT CONFIRMED
    // ========================================

    if (
      status ===
      "Confirmed"
    ) {
      alert(
        "Payment confirmed! Your Premium membership is now active."
      );

      /**
       * Reload the page so PremiumContext
       * retrieves the newly activated
       * subscription.
       */

      window.location.reload();

      return;
    }

    // ========================================
    // PAYMENT STILL PENDING
    // ========================================

    if (
      status ===
        "Pending" ||
      status ===
        "Processing" ||
      status ===
        "PartiallyPaid"
    ) {
      alert(
        `Payment is still ${status}. Please wait for confirmation.`
      );

      return;
    }

    // ========================================
    // FAILED / CANCELLED / REFUNDED
    // ========================================

    alert(
      `Payment status: ${status}`
    );

  } catch (error) {
    console.error(
      "Check payment status error:",
      error
    );

    alert(
      error instanceof Error
        ? error.message
        : "Unable to check payment status."
    );
  } finally {
    setCheckLoading(false);
  }
}

  /**
   * ==========================================
   * CANCEL PENDING PREMIUM PAYMENT
   * ==========================================
   */

  async function handleCancelPending() {
    console.log("🔥 CANCEL BUTTON FUNCTION CALLED");
    if (
      !backendSubscription ||
      backendSubscription.status !==
        "Pending"
    ) {
      return;
    }

    const confirmed =
      window.confirm(
        "Are you sure you want to cancel your pending Premium payment?"
      );

    if (!confirmed) {
      return;
    }

    try {
      setCancelLoading(true);

      const result =
        await premiumApiService.cancelPendingPremium();

      if (!result.success) {
        alert(
          result.message ||
            "Unable to cancel the pending payment."
        );

        return;
      }

      /**
       * Update backend state immediately.
       */

      setBackendSubscription(
        result.data
      );

      /**
       * Clear payment information.
       */

      setPaymentData(null);

      /**
       * Close any open checkout.
       */

      setCheckoutOpen(false);

      setSelectedPlan(null);

      alert(
        "Your pending Premium payment has been cancelled successfully."
      );

    } catch (error) {
      console.error(
        "Cancel Premium payment error:",
        error
      );

      alert(
        error instanceof Error
          ? error.message
          : "Unable to cancel the pending payment."
      );
    } finally {
      setCancelLoading(false);
    }
  }

  /**
   * ==========================================
   * RENEW PREMIUM
   * ==========================================
   */

  function handleRenew() {
    if (!subscription.plan) {
      return;
    }

    /**
     * Do not create another payment if
     * backend already has a pending payment.
     */

    if (
      backendSubscription?.status ===
      "Pending"
    ) {
      alert(
        "You already have a pending Premium payment. Please complete or cancel it first."
      );

      return;
    }

    setSelectedPlan(
      subscription.plan
    );

    setCheckoutOpen(true);
  }

  /**
   * ==========================================
   * CLOSE CHECKOUT
   * ==========================================
   */

  function closeCheckout() {
    if (loading) {
      return;
    }

    setCheckoutOpen(false);

    setSelectedPlan(null);
  }

  /**
   * ==========================================
   * CLOSE PAYMENT CREATED SCREEN
   * ==========================================
   */

  function closeSuccess() {
    setSuccessOpen(false);

    setSelectedPlan(null);
    setPaymentData(null);
  }

  /**
   * ==========================================
   * PENDING PAYMENT PLAN
   * ==========================================
   *
   * Converts the backend plan name into
   * the frontend PremiumPlan object.
   */

  const pendingPlan =
    backendSubscription?.status ===
      "Pending"
      ? PREMIUM_PLANS.find(
          (plan) =>
            plan.name ===
            backendSubscription.plan
        ) || null
      : null;

  /**
   * ==========================================
   * PAGE
   * ==========================================
   */

  return (
    <section className="bg-slate-50 min-h-screen py-16">

      <Container>

        {/* ======================================
            HERO
        ====================================== */}

       <PremiumHero
  plans={PREMIUM_PLANS}
  onSelect={handleSelectPlan}
/>

        {/* ======================================
            PENDING PREMIUM PAYMENT
        ====================================== */}

        {backendSubscription?.status ===
          "Pending" && (
          <div className="my-10 rounded-2xl border border-yellow-300 bg-yellow-50 p-6">

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">

              {/* ==================================
                  PENDING INFORMATION
              ================================== */}

              <div>

                <h2 className="text-2xl font-bold text-yellow-800">
                  Pending Premium Payment
                </h2>

                <p className="text-yellow-700 mt-2">
                  You already have a Premium
                  payment waiting for confirmation.
                </p>

                <div className="mt-4 space-y-2 text-sm text-gray-700">

                  <p>
                    <strong>
                      Plan:
                    </strong>{" "}
                    {backendSubscription.plan}
                  </p>

                  <p>
                    <strong>
                      Amount:
                    </strong>{" "}
                    $
                    {backendSubscription.priceUsd.toLocaleString()}{" "}
                    USD
                  </p>

                  {backendSubscription.paymentId &&
                    typeof backendSubscription.paymentId !==
                      "string" && (
                      <>
                        <p>
                          <strong>
                            Cryptocurrency:
                          </strong>{" "}
                          {
                            backendSubscription
                              .paymentId
                              .cryptoCurrency
                          }
                        </p>

                        <p>
                          <strong>
                            Network:
                          </strong>{" "}
                          {
                            backendSubscription
                              .paymentId
                              .cryptoNetwork
                          }
                        </p>

                        {backendSubscription
                          .paymentId
                          .cryptoAmount !==
                          undefined && (
                          <p>
                            <strong>
                              Crypto Amount:
                            </strong>{" "}
                            {
                              backendSubscription
                                .paymentId
                                .cryptoAmount
                            }
                          </p>
                        )}

                        {backendSubscription
                          .paymentId
                          .walletAddress && (
                          <p className="break-all">
                            <strong>
                              Payment Address:
                            </strong>{" "}
                            {
                              backendSubscription
                                .paymentId
                                .walletAddress
                            }
                          </p>
                        )}

                        {backendSubscription
                          .paymentId
                          .providerPaymentId && (
                          <p>
                            <strong>
                              NOWPayments ID:
                            </strong>{" "}
                            {
                              backendSubscription
                                .paymentId
                                .providerPaymentId
                            }
                          </p>
                        )}

                        <p>
                          <strong>
                            Payment Status:
                          </strong>{" "}
                          <span className="font-semibold text-yellow-700">
                            {
                              backendSubscription
                                .paymentId
                                .status
                            }
                          </span>
                        </p>
                      </>
                    )}

                  <p>
                    <strong>
                      Subscription Status:
                    </strong>{" "}
                    <span className="font-semibold text-yellow-700">
                      Pending
                    </span>
                  </p>

                </div>

              </div>

              {/* ==================================
                  ACTIONS
              ================================== */}

              <div className="flex flex-col sm:flex-row gap-3">

                {/* ==================================
                    CONTINUE PAYMENT
                ================================== */}

                <button
                  type="button"
                  onClick={() => {
                    if (!pendingPlan) {
                      return;
                    }

                    setSelectedPlan(
                      pendingPlan
                    );

                    setCheckoutOpen(
                      true
                    );
                  }}
                  className="px-5 py-3 rounded-xl bg-blue-600 text-white hover:bg-blue-700 transition"
                >
                  Continue Payment
                </button>

                {/* ==================================
                    CANCEL PAYMENT
                ================================== */}

                <button
                  type="button"
                  disabled={
                    cancelLoading
                  }
                  onClick={
                    handleCancelPending
                  }
                  className="px-5 py-3 rounded-xl border border-red-300 text-red-700 hover:bg-red-50 disabled:opacity-50 transition"
                >
                  {cancelLoading
                    ? "Cancelling..."
                    : "Cancel Pending Payment"}
                </button>

              </div>

            </div>

          </div>
        )}

        {/* ======================================
            PREMIUM PLANS
        ====================================== */}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 my-16">

          {PREMIUM_PLANS.map(
            (plan) => (
              <PremiumCard
                key={plan.id}
                plan={plan}
                onSelect={
                  handleSelectPlan
                }
              />
            )
          )}

        </div>

        {/* ======================================
            PLAN COMPARISON
        ====================================== */}

        <PremiumComparison
          plans={PREMIUM_PLANS}
          onSelect={
            handleSelectPlan
          }
        />

        {/* ======================================
            FAQ
        ====================================== */}

        <PremiumFAQ />

        {/* ======================================
            CURRENT PREMIUM STATUS
        ====================================== */}

        <PremiumStatus
          subscription={
            subscription
          }
          daysRemaining={
            daysRemaining
          }
          onRenew={
            handleRenew
          }
        />

        {/* ======================================
            PREMIUM ANALYTICS
        ====================================== */}

        <PremiumAnalytics
          subscription={
            subscription
          }
          daysRemaining={
            daysRemaining
          }
        />

        {/* ======================================
            EXPIRATION REMINDER
        ====================================== */}

        <PremiumReminder
          active={
            subscription.active
          }
          daysRemaining={
            daysRemaining
          }
          onRenew={
            handleRenew
          }
        />

        {/* ======================================
            PREMIUM HISTORY
        ====================================== */}

        <PremiumHistory
          userId={userId}
        />

        {/* ======================================
            CHECKOUT
        ====================================== */}

        <PremiumCheckout
          open={checkoutOpen}
          plan={selectedPlan}
          onClose={
            closeCheckout
          }
          onConfirm={
            handleConfirmPayment
          }
        />

        {/* ======================================
            PAYMENT CREATED / PENDING
        ====================================== */}

      <PremiumSuccess
  open={successOpen}
  plan={selectedPlan}
  payment={paymentData}
  onClose={closeSuccess}
  onCheckStatus={
    handleCheckStatus
  }
  onCancelPayment={
    handleCancelPending
  }
  checkingStatus={
    checkLoading
  }
  cancellingPayment={
    cancelLoading
  }
/>

      </Container>

    </section>
  );
}