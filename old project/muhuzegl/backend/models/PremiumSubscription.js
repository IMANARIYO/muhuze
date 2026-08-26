import mongoose from "mongoose";

const premiumSubscriptionSchema =
  new mongoose.Schema(
    {
      // ==========================================
      // USER
      // ==========================================

      userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        required: true,
        index: true,
      },

      // ==========================================
      // PREMIUM PLAN
      // ==========================================

      plan: {
        type: String,
        enum: [
          "Monthly",
          "Annual",
        ],
        required: true,
      },

      // ==========================================
      // PAYMENT
      // ==========================================

      paymentId: {
  type: mongoose.Schema.Types.ObjectId,
  ref: "Payment",
  default: null,
  index: true,
},

      // ==========================================
      // PRICE
      // ==========================================

      priceUsd: {
        type: Number,
        required: true,
        min: 0,
      },

      // ==========================================
      // MEMBERSHIP PERIOD
      // ==========================================

      startDate: {
        type: Date,
        default: null,
      },

      expiryDate: {
        type: Date,
        default: null,
        index: true,
      },

      // ==========================================
      // STATUS
      // ==========================================
      //
      // Pending
      // Active
      // Expired
      // Cancelled
      //

      status: {
        type: String,
        enum: [
          "Pending",
          "Active",
          "Expired",
          "Cancelled",
        ],
        default: "Pending",
        index: true,
      },

      // ==========================================
      // SELLER COMMISSION
      // ==========================================
      //
      // Premium Seller = 7%
      // Basic Seller   = 12%
      //
      // This is stored as a record of the
      // membership benefit.
      //
      // Actual seller commission logic should
      // always verify the current Premium status.
      //

      sellerCommissionRate: {
        type: Number,
        default: 7,
        min: 0,
        max: 100,
      },

      // ==========================================
      // REFERRAL PARTICIPATION
      // ==========================================
      //
      // Premium members are eligible to
      // participate in the referral program.
      //
      // This does NOT guarantee income.
      //

      referralCommissionEligible: {
        type: Boolean,
        default: true,
      },

      // ==========================================
      // ACTIVATION
      // ==========================================

      activatedAt: {
        type: Date,
        default: null,
      },

      // ==========================================
      // EXPIRATION
      // ==========================================

      expiredAt: {
        type: Date,
        default: null,
      },

      // ==========================================
      // CANCELLATION
      // ==========================================

      cancelledAt: {
        type: Date,
        default: null,
      },

      cancellationReason: {
        type: String,
        default: "",
        trim: true,
      },
    },
    {
      timestamps: true,
    }
  );

// ==========================================
// INDEXES
// ==========================================

// Quickly find a user's active subscription
premiumSubscriptionSchema.index({
  userId: 1,
  status: 1,
});

// Quickly find subscriptions that may have expired
premiumSubscriptionSchema.index({
  status: 1,
  expiryDate: 1,
});

const PremiumSubscription =
  mongoose.model(
    "PremiumSubscription",
    premiumSubscriptionSchema
  );

export default PremiumSubscription;