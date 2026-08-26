import mongoose from "mongoose";

const walletSchema = new mongoose.Schema(
  {
    // ==========================================
    // USER
    // ==========================================

    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      unique: true,
      index: true,
    },

    // ==========================================
    // RWF WALLET
    // ==========================================

    rwf: {
      balance: {
        type: Number,
        default: 0,
        min: 0,
      },

      pendingBalance: {
        type: Number,
        default: 0,
        min: 0,
      },

      totalEarned: {
        type: Number,
        default: 0,
        min: 0,
      },

      totalWithdrawn: {
        type: Number,
        default: 0,
        min: 0,
      },
    },

    // ==========================================
    // USD-BASED WALLET
    // ==========================================
    //
    // USD + USDT + USDC are represented here.
    //
    // Examples:
    //
    // $50 USD
    // + 30 USDT
    // + 20 USDC
    //
    // = $100 USD-based balance
    //
    // Original payment asset is stored
    // separately in WalletTransaction.
    // ==========================================

    usd: {
      balance: {
        type: Number,
        default: 0,
        min: 0,
      },

      pendingBalance: {
        type: Number,
        default: 0,
        min: 0,
      },

      totalEarned: {
        type: Number,
        default: 0,
        min: 0,
      },

      totalWithdrawn: {
        type: Number,
        default: 0,
        min: 0,
      },
    },

    // ==========================================
    // WALLET STATUS
    // ==========================================

    status: {
      type: String,
      enum: [
        "Active",
        "Suspended",
        "Frozen",
      ],
      default: "Active",
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model(
  "Wallet",
  walletSchema
);