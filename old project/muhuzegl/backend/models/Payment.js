import mongoose from "mongoose";

const paymentSchema = new mongoose.Schema(
  {
    // User making the payment
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
    },

    // Order or other activity being paid for
    sourceId: {
      type: mongoose.Schema.Types.ObjectId,
      required: true,
    },

    // What is being paid for
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

    // MUHUZE price in USD
    usdAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    // Payment method
    paymentMethod: {
      type: String,
      enum: ["CARD", "CRYPTO"],
      required: true,
    },

    // =========================
    // CARD PAYMENT INFORMATION
    // =========================

    cardBrand: {
      type: String,
      enum: ["VISA", "MASTERCARD"],
    },

    // Only the last 4 digits are stored.
    // Never store the full card number or CVV.
    cardLast4: {
      type: String,
      trim: true,
    },

    // =========================
    // CRYPTO PAYMENT INFORMATION
    // =========================

    cryptoCurrency: {
      type: String,
      enum: ["USDT", "USDC"],
    },

    cryptoNetwork: {
      type: String,
      enum: [
        "BEP20",
        "ERC20",
      ],
    },

    cryptoAmount: {
      type: Number,
      min: 0,
    },

    walletAddress: {
      type: String,
      trim: true,
    },

    transactionHash: {
      type: String,
      trim: true,
    },

    // =========================
    // PAYMENT PROVIDER
    // =========================

    provider: {
      type: String,
      trim: true,
    },

    providerPaymentId: {
      type: String,
      trim: true,
    },

    // =========================
    // PAYMENT STATUS
    // =========================

    status: {
      type: String,
      enum: [
        "Pending",
        "Processing",
        "PartiallyPaid",
        "Confirmed",
        "Failed",
        "Cancelled",
        "Refunded",
      ],
      default: "Pending",
    },

    // When payment was confirmed
    confirmedAt: {
      type: Date,
    },

    // When payment was refunded
    refundedAt: {
      type: Date,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model(
  "Payment",
  paymentSchema
);