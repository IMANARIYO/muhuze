import mongoose from "mongoose";

const referralCommissionSchema = new mongoose.Schema(
  {
    // The user receiving the referral commission
    referrer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    // The user whose activity generated the commission
    referredUser: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    // The revenue transaction that generated this commission
    revenueTransaction: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "RevenueTransaction",
      required: true,
    },

    // What generated the revenue
    sourceType: {
      type: String,
      enum: [
        "PRODUCT_SALE",
        "PREMIUM",
        "PROMOTION",
        "ADVERTISING",
      ],
      required: true,
    },

    // Referral level
    level: {
      type: Number,
      enum: [1, 2, 3],
      required: true,
    },

    // Referral rate
    // Level 1 = 12%
    // Level 2 = 5%
    // Level 3 = 3%
    commissionRate: {
      type: Number,
      required: true,
      min: 0,
    },

    // MUHUZE revenue used for the calculation
    revenueAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    // 20% of MUHUZE revenue
    referralPoolAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    // Actual commission earned by this referrer
    commissionAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    // Internal accounting currency
    currency: {
      type: String,
      required: true,
      uppercase: true,
      trim: true,
      default: "USD",
    },

    // Commission lifecycle
    status: {
      type: String,
      enum: [
        "Pending",
        "Available",
        "Reversed",
        "Cancelled",
      ],
      default: "Pending",
    },

    // When the commission becomes available
    availableAt: {
      type: Date,
    },

    // Optional explanation/reference
    description: {
      type: String,
      trim: true,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model(
  "ReferralCommission",
  referralCommissionSchema
);