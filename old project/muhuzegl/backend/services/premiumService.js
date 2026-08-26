import mongoose from "mongoose";

import User from "../models/User.js";
import PremiumSubscription from "../models/PremiumSubscription.js";
import Payment from "../models/Payment.js";

/**
 * =====================================================
 * PREMIUM SERVICE
 * =====================================================
 *
 * Individual Premium Membership
 *
 * Monthly:
 *   $10
 *   30 days
 *
 * Annual:
 *   $100
 *   365 days
 *
 * Premium Seller Commission:
 *   7%
 *
 * Basic Seller Commission:
 *   12%
 *
 * Premium members are eligible to participate
 * in the referral commission system.
 *
 * IMPORTANT:
 *
 * Premium membership does NOT guarantee income.
 *
 * Referral commissions require qualifying
 * economic activity that generates eligible
 * MUHUZE revenue.
 * =====================================================
 */

class PremiumService {
  // ===================================================
  // PLAN CONFIGURATION
  // ===================================================

  plans = {
    Monthly: {
      priceUsd: 10,
      durationDays: 30,
      sellerCommissionRate: 7,
    },

    Annual: {
      priceUsd: 100,
      durationDays: 365,
      sellerCommissionRate: 7,
    },
  };

  // ===================================================
  // GET PLAN CONFIGURATION
  // ===================================================

  getPlanConfig(plan) {
    const config = this.plans[plan];

    if (!config) {
      throw new Error(
        `Unsupported Premium plan: ${plan}`
      );
    }

    return config;
  }

  // ===================================================
  // VALIDATE PLAN
  // ===================================================

  validatePlan(plan) {
    return Boolean(
      this.plans[plan]
    );
  }

  // ===================================================
  // CALCULATE EXPIRY DATE
  // ===================================================

  calculateExpiryDate(
    startDate,
    durationDays
  ) {
    const expiryDate =
      new Date(startDate);

    expiryDate.setDate(
      expiryDate.getDate() +
        durationDays
    );

    return expiryDate;
  }

  // ===================================================
  // GET ACTIVE SUBSCRIPTION
  // ===================================================

  async getActiveSubscription(
    userId
  ) {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid user ID."
      );
    }

    return await PremiumSubscription.findOne(
      {
        userId,
        status: "Active",
        expiryDate: {
          $gt: new Date(),
        },
      }
    ).sort({
      expiryDate: -1,
    });
  }

  // ===================================================
  // CHECK PREMIUM STATUS
  // ===================================================

  async isPremiumActive(
    userId
  ) {
    const subscription =
      await this.getActiveSubscription(
        userId
      );

    return Boolean(
      subscription
    );
  }

  // ===================================================
  // CREATE PENDING SUBSCRIPTION
  // ===================================================
  //
  // This happens BEFORE payment confirmation.
  //
  // The subscription remains Pending until
  // PaymentService confirms the payment.
  //

  async createPendingSubscription({
    userId,
    plan,
  }) {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid user ID."
      );
    }

    const config =
      this.getPlanConfig(plan);

    const user =
      await User.findById(userId);

    if (!user) {
      throw new Error(
        "User not found."
      );
    }

    const subscription =
      await PremiumSubscription.create({
        userId,

        plan,

        priceUsd:
          config.priceUsd,

        status: "Pending",

        sellerCommissionRate:
          config.sellerCommissionRate,

        referralCommissionEligible:
          true,
      });

    return subscription;
  }

  // ===================================================
  // ACTIVATE PREMIUM FROM CONFIRMED PAYMENT
  // ===================================================
  //
  // This is called ONLY after the payment has
  // reached Confirmed status.
  //

  async activateFromPayment(
    paymentId
  ) {
    if (
      !mongoose.Types.ObjectId.isValid(
        paymentId
      )
    ) {
      throw new Error(
        "Invalid payment ID."
      );
    }

    // -----------------------------------------------
    // FIND PAYMENT
    // -----------------------------------------------

    const payment =
      await Payment.findById(
        paymentId
      );

    if (!payment) {
      throw new Error(
        "Payment not found."
      );
    }

    // -----------------------------------------------
    // PAYMENT MUST BE PREMIUM
    // -----------------------------------------------

    if (
      payment.sourceType !==
      "PREMIUM"
    ) {
      throw new Error(
        "This payment is not a Premium membership payment."
      );
    }

    // -----------------------------------------------
    // PAYMENT MUST BE CONFIRMED
    // -----------------------------------------------

    if (
      payment.status !==
      "Confirmed"
    ) {
      throw new Error(
        "Premium cannot be activated before payment is confirmed."
      );
    }

    // -----------------------------------------------
    // FIND PENDING SUBSCRIPTION
    // -----------------------------------------------

    const subscription =
      await PremiumSubscription.findOne(
        {
          paymentId:
            payment._id,
        }
      );

    if (!subscription) {
      throw new Error(
        "Premium subscription linked to this payment was not found."
      );
    }
    // -----------------------------------------------
    // SUBSCRIPTION MUST STILL BE PENDING
    // -----------------------------------------------
    //
    // A cancelled Premium subscription must NEVER
    // be activated by a delayed NOWPayments webhook.
    //

    if (
      subscription.status !==
      "Pending"
    ) {
      console.log(
        `Premium activation skipped. Subscription ${subscription._id} is ${subscription.status}.`
      );

      return subscription;
    }
    // -----------------------------------------------
    // IDEMPOTENCY
    // -----------------------------------------------
    //
    // If NOWPayments sends the same confirmed
    // notification again, do not activate twice.
    //

    if (
      subscription.status ===
      "Active"
    ) {
      return subscription;
    }

    // -----------------------------------------------
    // PLAN CONFIGURATION
    // -----------------------------------------------

    const config =
      this.getPlanConfig(
        subscription.plan
      );

    // -----------------------------------------------
    // START DATE
    // -----------------------------------------------

    const startDate =
      new Date();

    // -----------------------------------------------
    // CHECK CURRENT PREMIUM
    // -----------------------------------------------

    const currentSubscription =
      await this.getActiveSubscription(
        subscription.userId
      );

    let expiryDate;

    // -----------------------------------------------
    // RENEWAL LOGIC
    // -----------------------------------------------
    //
    // If the user already has active Premium,
    // extend from the current expiry date.
    //
    // Otherwise start from today.
    //

    if (
      currentSubscription &&
      currentSubscription.expiryDate >
        startDate
    ) {
      expiryDate =
        this.calculateExpiryDate(
          currentSubscription.expiryDate,
          config.durationDays
        );
    } else {
      expiryDate =
        this.calculateExpiryDate(
          startDate,
          config.durationDays
        );
    }

    // -----------------------------------------------
    // ACTIVATE SUBSCRIPTION
    // -----------------------------------------------

    subscription.status =
      "Active";

    subscription.startDate =
      startDate;

    subscription.expiryDate =
      expiryDate;

    subscription.activatedAt =
      startDate;

    subscription.expiredAt =
      null;

    subscription.cancelledAt =
      null;

    subscription.cancellationReason =
      "";

    subscription.sellerCommissionRate =
      config.sellerCommissionRate;

    subscription.referralCommissionEligible =
      true;

    await subscription.save();

    // -----------------------------------------------
    // UPDATE USER PREMIUM STATUS
    // -----------------------------------------------

    await this.updateUserPremiumStatus(
      subscription.userId,
      {
        active: true,

        plan:
          subscription.plan,

        startDate,

        expiryDate,

        referralCommissionEligible:
          true,

        sellerCommissionRate:
          config.sellerCommissionRate,
      }
    );

    return subscription;
  }

  // ===================================================
  // UPDATE USER PREMIUM STATUS
  // ===================================================

  async updateUserPremiumStatus(
    userId,
    premiumData
  ) {
    const user =
      await User.findById(
        userId
      );

    if (!user) {
      throw new Error(
        "User not found."
      );
    }

    user.premium = {
      active:
        premiumData.active,

      plan:
        premiumData.plan,

      startDate:
        premiumData.startDate,

      expiryDate:
        premiumData.expiryDate,

      referralCommissionEligible:
        premiumData.referralCommissionEligible,

      sellerCommissionRate:
        premiumData.sellerCommissionRate,
    };

    await user.save();

    return user;
  }

  // ===================================================
  // EXPIRE ONE SUBSCRIPTION
  // ===================================================

  async expireSubscription(
    subscriptionId
  ) {
    if (
      !mongoose.Types.ObjectId.isValid(
        subscriptionId
      )
    ) {
      throw new Error(
        "Invalid subscription ID."
      );
    }

    const subscription =
      await PremiumSubscription.findById(
        subscriptionId
      );

    if (!subscription) {
      throw new Error(
        "Premium subscription not found."
      );
    }

    if (
      subscription.status !==
      "Active"
    ) {
      return subscription;
    }

    // -----------------------------------------------
    // MARK SUBSCRIPTION EXPIRED
    // -----------------------------------------------

    subscription.status =
      "Expired";

    subscription.expiredAt =
      new Date();

    subscription.referralCommissionEligible =
      false;

    await subscription.save();

    // -----------------------------------------------
    // CHECK WHETHER USER HAS ANOTHER
    // ACTIVE SUBSCRIPTION
    // -----------------------------------------------

    const anotherActiveSubscription =
      await this.getActiveSubscription(
        subscription.userId
      );

    if (
      anotherActiveSubscription
    ) {
      await this.updateUserPremiumStatus(
        subscription.userId,
        {
          active: true,

          plan:
            anotherActiveSubscription.plan,

          startDate:
            anotherActiveSubscription.startDate,

          expiryDate:
            anotherActiveSubscription.expiryDate,

          referralCommissionEligible:
            true,

          sellerCommissionRate: 7,
        }
      );

      return subscription;
    }

    // -----------------------------------------------
    // NO ACTIVE PREMIUM REMAINS
    // -----------------------------------------------

    await this.updateUserPremiumStatus(
      subscription.userId,
      {
        active: false,

        plan: null,

        startDate: null,

        expiryDate: null,

        referralCommissionEligible:
          false,

        sellerCommissionRate: 12,
      }
    );

    return subscription;
  }

  // ===================================================
  // EXPIRE DUE SUBSCRIPTIONS
  // ===================================================
  //
  // This can later be called by a cron job.
  //

  async expireDueSubscriptions() {
    const now =
      new Date();

    const subscriptions =
      await PremiumSubscription.find(
        {
          status: "Active",

          expiryDate: {
            $lte: now,
          },
        }
      );

    const results = [];

    for (
      const subscription
      of subscriptions
    ) {
      try {
        const expired =
          await this.expireSubscription(
            subscription._id
          );

        results.push(
          expired
        );
      } catch (error) {
        console.error(
          "PREMIUM EXPIRATION ERROR:",
          error
        );
      }
    }

    return results;
  }

  // ===================================================
  // GET USER SUBSCRIPTION HISTORY
  // ===================================================

  async getUserSubscriptions(
    userId
  ) {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid user ID."
      );
    }

    return await PremiumSubscription.find(
      {
        userId,
      }
    )
      .sort({
        createdAt: -1,
      })
      .populate(
        "paymentId"
      );
  }

  // ===================================================
  // GET ONE SUBSCRIPTION
  // ===================================================

  async getSubscription(
    subscriptionId
  ) {
    if (
      !mongoose.Types.ObjectId.isValid(
        subscriptionId
      )
    ) {
      throw new Error(
        "Invalid subscription ID."
      );
    }

    return await PremiumSubscription.findById(
      subscriptionId
    ).populate(
      "paymentId"
    );
  }
    // ===================================================
  // CANCEL PENDING PREMIUM SUBSCRIPTION
  // ===================================================
  //
  // A user may cancel a Premium payment only while
  // the subscription is still Pending.
  //
  // The subscription is NOT deleted.
  // It remains in Premium History as Cancelled.
  //

  async cancelPendingSubscription(userId) {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid user ID."
      );
    }

    // -----------------------------------------------
    // FIND USER'S PENDING SUBSCRIPTION
    // -----------------------------------------------

    const subscription =
      await PremiumSubscription.findOne({
        userId,
        status: "Pending",
      }).sort({
        createdAt: -1,
      });

    if (!subscription) {
      throw new Error(
        "No pending Premium subscription found."
      );
    }

    // -----------------------------------------------
    // FIND LINKED PAYMENT
    // -----------------------------------------------

    let payment = null;

    if (subscription.paymentId) {
      payment =
        await Payment.findById(
          subscription.paymentId
        );
    }

    // -----------------------------------------------
    // CANCEL PAYMENT
    // -----------------------------------------------

    if (payment) {
      if (
        payment.status ===
        "Pending"
      ) {
        payment.status =
          "Cancelled";

        await payment.save();
      }
    }

    // -----------------------------------------------
    // CANCEL SUBSCRIPTION
    // -----------------------------------------------

    subscription.status =
      "Cancelled";

    subscription.cancelledAt =
      new Date();

    subscription.cancellationReason =
      "Cancelled by user before payment confirmation.";

    subscription.referralCommissionEligible =
      false;

    await subscription.save();

    // -----------------------------------------------
    // RETURN UPDATED SUBSCRIPTION
    // -----------------------------------------------

    return subscription;
  }
}

export default new PremiumService();