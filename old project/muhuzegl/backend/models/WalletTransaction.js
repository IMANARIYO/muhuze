import mongoose from "mongoose";

const walletTransactionSchema =
  new mongoose.Schema(
    {
      // ==========================================
      // USER
      // ==========================================

      userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        required: true,
      },

      // ==========================================
      // TRANSACTION TYPE
      // ==========================================

      type: {
        type: String,
        enum: [
          "REFERRAL_COMMISSION",
          "SELLER_REVENUE",
          "COMMISSION_REVERSAL",
          "WITHDRAWAL",
          "REFUND",
          "ADJUSTMENT",
          "DEPOSIT",
          "PAYMENT",
        ],
        required: true,
      },

      // ==========================================
      // AMOUNT
      // ==========================================

      amount: {
        type: Number,
        required: true,
      },

      // ==========================================
      // ORIGINAL PAYMENT ASSET
      // ==========================================
      //
      // What was actually used?
      //
      // RWF
      // USD
      // USDT
      // USDC
      // BTC
      //
      // ==========================================

      asset: {
        type: String,
        required: true,
        uppercase: true,
        trim: true,
        enum: [
          "RWF",
          "USD",
          "USDT",
          "USDC",
          "BTC",
        ],
      },

      // ==========================================
      // ACCOUNTING CURRENCY
      // ==========================================
      //
      // RWF stays RWF.
      //
      // USD / USDT / USDC
      // become USD accounting.
      //
      // ==========================================

      currency: {
        type: String,
        required: true,
        uppercase: true,
        trim: true,
        enum: [
          "RWF",
          "USD",
        ],
      },

      // ==========================================
      // USD/RWF EQUIVALENT
      // ==========================================
      //
      // Amount represented in accounting currency.
      //
      // Example:
      //
      // 30 USDT
      //
      // asset = USDT
      // amount = 30
      // currency = USD
      // accountingAmount = 30
      //
      // ==========================================

      accountingAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // ==========================================
      // EXCHANGE RATE
      // ==========================================
      //
      // Example:
      //
      // 1 USDT = 1 USD
      //
      // 1 USD = 1 USD
      //
      // RWF may be:
      //
      // 1 USD = 1,450 RWF
      //
      // ==========================================

      exchangeRate: {
        type: Number,
        required: true,
        min: 0,
      },

      // ==========================================
      // REFERENCE
      // ==========================================

      referenceId: {
        type: mongoose.Schema.Types.ObjectId,
      },

      referenceType: {
        type: String,
        enum: [
          "ReferralCommission",
          "Withdrawal",
          "RevenueTransaction",
          "Order",
          "Payment",
        ],
      },

      // ==========================================
      // STATUS
      // ==========================================

      status: {
        type: String,
        enum: [
          "Pending",
          "Completed",
          "Reversed",
          "Cancelled",
        ],
        default: "Completed",
      },

      // ==========================================
      // DESCRIPTION
      // ==========================================

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
  "WalletTransaction",
  walletTransactionSchema
);