import PremiumSubscription from "../models/PremiumSubscription.js";
import paymentService from "../services/paymentService.js";
import premiumService from "../services/premiumService.js";
import User from "../models/User.js";
/**
 * ==========================================
 * PREMIUM PLAN CONFIGURATION
 * ==========================================
 *
 * Individual Premium only for now.
 *
 * Monthly = $10
 * Annual  = $100
 */

const PREMIUM_PLANS = {
  Monthly: {
    priceUsd: 10,
    durationDays: 30,
  },

  Annual: {
    priceUsd: 100,
    durationDays: 365,
  },
};

/**
 * ==========================================
 * CREATE PREMIUM SUBSCRIPTION
 * ==========================================
 *
 * Flow:
 *
 * User selects plan
 *       ↓
 * Create Pending Subscription
 *       ↓
 * Create Payment
 *       ↓
 * NOWPayments
 *       ↓
 * Return payment information
 *
 * IMPORTANT:
 *
 * Premium is NOT activated here.
 *
 * Activation happens only after
 * NOWPayments confirms payment.
 */

const createPremiumSubscription = async (req, res) => {
  try {
    /**
     * Authenticated user
     */
    const userId = req.user?._id;

    if (!userId) {
      return res.status(401).json({
        success: false,
        message: "Authentication required.",
      });
    }

    const { plan } = req.body;

    /**
     * Validate plan
     */
    if (!plan || !PREMIUM_PLANS[plan]) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid Premium plan. Choose Monthly or Annual.",
      });
    }

    const selectedPlan = PREMIUM_PLANS[plan];

    /**
     * Make sure user exists
     */
    const user = await User.findById(userId);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found.",
      });
    }

    /**
     * Check for an already pending subscription
     */
    const pendingSubscription =
      await PremiumSubscription.findOne({
        userId,
        status: "Pending",
      });

    if (pendingSubscription) {
      return res.status(409).json({
        success: false,
        message:
          "You already have a pending Premium payment.",
        data: pendingSubscription,
      });
    }

    /**
     * Check active Premium
     */
    const activeSubscription =
      await PremiumSubscription.findOne({
        userId,
        status: "Active",
      });

    if (activeSubscription) {
      return res.status(409).json({
        success: false,
        message:
          "You already have an active Premium membership.",
        data: activeSubscription,
      });
    }

    /**
     * ==========================================
     * CREATE PENDING SUBSCRIPTION
     * ==========================================
     */

    const subscription =
  await premiumService.createPendingSubscription({
    userId,
    plan,
  });

    try {
      /**
       * ========================================
       * CREATE PAYMENT
       * ========================================
       */

      const payment =
  await paymentService.createPayment({
    userId,

    sourceId:
      subscription._id,

    sourceType:
      "PREMIUM",

    usdAmount:
      selectedPlan.priceUsd,

    paymentMethod:
      "CRYPTO",

    cryptoCurrency:
      req.body.cryptoCurrency,

    cryptoNetwork:
      req.body.cryptoNetwork,

    description:
      `MUHUZE ${plan} Premium Membership`,
  });

      /**
       * ========================================
       * CONNECT PAYMENT TO SUBSCRIPTION
       * ========================================
       */

      subscription.paymentId =
        payment.payment._id;

      await subscription.save();

      /**
       * ========================================
       * RETURN CHECKOUT DATA
       * ========================================
       */

      return res.status(201).json({
        success: true,

        message:
          "Premium subscription created. Complete payment to activate membership.",

        data: {
          subscription,

          payment,
        },
      });
    } catch (paymentError) {
      /**
       * Payment creation failed.
       *
       * Do not leave a useless Pending
       * subscription behind.
       */

      await PremiumSubscription.findByIdAndDelete(
        subscription._id
      );

      throw paymentError;
    }
  } catch (error) {
    console.error(
      "Create Premium subscription error:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        error.message ||
        "Unable to create Premium subscription.",
    });
  }
};

/**
 * ==========================================
 * GET CURRENT PREMIUM SUBSCRIPTION
 * ==========================================
 */

const getMyPremiumSubscription = async (
  req,
  res
) => {
  try {
    const userId = req.user?._id;

    if (!userId) {
      return res.status(401).json({
        success: false,
        message: "Authentication required.",
      });
    }

    const subscription =
      await PremiumSubscription.findOne({
        userId,
      })
        .sort({
          createdAt: -1,
        })
        .populate("paymentId");

    return res.json({
      success: true,
      data: subscription,
    });
  } catch (error) {
    console.error(
      "Get Premium subscription error:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        error.message ||
        "Unable to get Premium subscription.",
    });
  }
};

/**
 * ==========================================
 * GET PREMIUM SUBSCRIPTION HISTORY
 * ==========================================
 */

const getPremiumHistory = async (
  req,
  res
) => {
  try {
    const userId = req.user?._id;

    if (!userId) {
      return res.status(401).json({
        success: false,
        message: "Authentication required.",
      });
    }

    const subscriptions =
      await PremiumSubscription.find({
        userId,
      })
        .sort({
          createdAt: -1,
        })
        .populate("paymentId");

    return res.json({
      success: true,

      count:
        subscriptions.length,

      data:
        subscriptions,
    });
  } catch (error) {
    console.error(
      "Get Premium history error:",
      error
    );

    return res.status(500).json({
      success: false,
      message:
        error.message ||
        "Unable to get Premium history.",
    });
  }
};
/**
 * ==========================================
 * CANCEL PENDING PREMIUM SUBSCRIPTION
 * ==========================================
 *
 * Cancels the user's pending Premium payment.
 *
 * The subscription is preserved in history
 * with status = Cancelled.
 *
 * Premium is never activated by cancellation.
 */

const cancelPendingPremium = async (
  req,
  res
) => {
  try {
    const userId =
      req.user?._id;

    if (!userId) {
      return res.status(401).json({
        success: false,
        message:
          "Authentication required.",
      });
    }

    const subscription =
      await premiumService.cancelPendingSubscription(
        userId
      );

    return res.json({
      success: true,

      message:
        "Pending Premium payment cancelled successfully.",

      data: subscription,
    });
  } catch (error) {
    console.error(
      "Cancel pending Premium error:",
      error
    );

    return res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to cancel pending Premium payment.",
    });
  }
};

export default {
  createPremiumSubscription,
  getMyPremiumSubscription,
  getPremiumHistory,
  cancelPendingPremium
};