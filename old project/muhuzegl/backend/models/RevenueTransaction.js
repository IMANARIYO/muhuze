import mongoose from "mongoose";

const sellerBreakdownSchema =
  new mongoose.Schema(
    {
      // Seller receiving the net earnings
      sellerId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        required: true,
      },

      // Seller's gross product amount
      lineAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // MUHUZE commission percentage
      commissionRate: {
        type: Number,
        required: true,
        min: 0,
      },

      // MUHUZE revenue generated from this seller
      revenueAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // Amount that belongs to the seller
      sellerEarning: {
        type: Number,
        required: true,
        min: 0,
      },
    },
    {
      _id: false,
    }
  );

const revenueTransactionSchema =
  new mongoose.Schema(
    {
      // User/customer responsible for the transaction
      userId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        required: true,
      },

      // Order/payment/source that generated revenue
      sourceId: {
        type: mongoose.Schema.Types.ObjectId,
        required: true,
      },

      // What generated MUHUZE revenue?
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

      // Original amount paid by customer
      sourceAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // Currency used by customer
      sourceCurrency: {
        type: String,
        required: true,
        uppercase: true,
        trim: true,
      },

      // Exchange rate used when revenue was created
      exchangeRate: {
        type: Number,
        required: true,
        min: 0,
      },

      // MUHUZE internal accounting amount
      accountingAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // Internal accounting currency
      accountingCurrency: {
        type: String,
        required: true,
        uppercase: true,
        trim: true,
        default: "USD",
      },

      // MUHUZE effective revenue percentage
      revenueRate: {
        type: Number,
        required: true,
        min: 0,
      },

      // Actual MUHUZE revenue
      revenueAmount: {
        type: Number,
        required: true,
        min: 0,
      },

      // =====================================================
      // SELLER BREAKDOWN
      // =====================================================
      //
      // For PRODUCT_SALE transactions this records exactly
      // how much each seller should receive.
      //
      // Example:
      //
      // Product sale = $100
      // MUHUZE commission = 12%
      //
      // sellerEarning = $88
      //
      sellerBreakdown: {
        type: [
          sellerBreakdownSchema,
        ],
        default: [],
      },

      // Whether this revenue can generate referral
      // commissions
      referralEligible: {
        type: Boolean,
        default: false,
      },

      // Revenue lifecycle
      status: {
        type: String,
        enum: [
          "Pending",
          "Completed",
          "Cancelled",
          "Reversed",
        ],
        default: "Pending",
      },

      // When revenue becomes financially available
      availableAt: {
        type: Date,
      },
    },
    {
      timestamps: true,
    }
  );

export default mongoose.model(
  "RevenueTransaction",
  revenueTransactionSchema
);