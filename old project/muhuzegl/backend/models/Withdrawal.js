import mongoose from "mongoose";

const withdrawalSchema = new mongoose.Schema(
  {
    /**
     * ==========================================
     * USER
     * ==========================================
     */

    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },

    /**
     * ==========================================
     * AMOUNTS
     * ==========================================
     *
     * requestedAmount = amount requested by user
     * feeAmount       = MUHUZE withdrawal fee
     * netAmount       = amount user receives
     */

    requestedAmount: {
      type: Number,
      required: true,
      min: 0.01,
    },

    feeRate: {
      type: Number,
      required: true,
      min: 0,
      default: 5,
    },

    feeAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    netAmount: {
      type: Number,
      required: true,
      min: 0,
    },

    /**
     * ==========================================
     * CURRENCY
     * ==========================================
     */

    currency: {
      type: String,
      required: true,
      uppercase: true,
      trim: true,
      default: "USD",
    },

    /**
     * ==========================================
     * PAYMENT METHOD
     * ==========================================
     */

    paymentMethod: {
      type: String,
      enum: [
        "MTN_MOBILE_MONEY",
        "AIRTEL_MONEY",
        "BANK_TRANSFER",
        "USDT",
        "USDC",
      ],
      required: true,
    },

    /**
     * ==========================================
     * CRYPTO NETWORK
     * ==========================================
     *
     * Required for USDT / USDC.
     */

    network: {
      type: String,
      enum: [
        "TRC20",
        "ERC20",
        "BEP20",
        "POLYGON",
        "ARBITRUM",
        "SOLANA",
      ],
    },

    /**
     * ==========================================
     * PAYMENT ACCOUNT
     * ==========================================
     *
     * Mobile money:
     * phone number
     *
     * Bank:
     * bank account
     *
     * Crypto:
     * wallet address
     */

    accountNumber: {
      type: String,
      required: true,
      trim: true,
    },

    /**
     * ==========================================
     * ACCOUNT NAME
     * ==========================================
     */

    accountName: {
      type: String,
      trim: true,
    },

    /**
     * ==========================================
     * STATUS
     * ==========================================
     */

    status: {
      type: String,
      enum: [
        "Pending",
        "Processing",
        "Completed",
        "Rejected",
        "Cancelled",
      ],
      default: "Pending",
    },

    /**
     * ==========================================
     * PROCESSING INFORMATION
     * ==========================================
     */

    processedAt: {
      type: Date,
    },

    processedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
    },

    rejectionReason: {
      type: String,
      trim: true,
    },

    /**
     * ==========================================
     * WALLET TRANSACTION
     * ==========================================
     */

    walletTransactionId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "WalletTransaction",
    },

    /**
     * ==========================================
     * DESCRIPTION
     * ==========================================
     */

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
  "Withdrawal",
  withdrawalSchema
);