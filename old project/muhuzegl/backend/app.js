import express from "express";
import cors from "cors";
import path from "path";
import mongoose from "mongoose";
import { fileURLToPath } from "url";

// =========================
// Routes
// =========================

import walletRoutes from "./routes/walletRoutes.js";
import userRoutes from "./routes/userRoutes.js";
import marketplaceRoutes from "./routes/marketplaceRoutes.js";
import orderRoutes from "./routes/orderRoutes.js";
import wishlistRoutes from "./routes/wishlistRoutes.js";
import cartRoutes from "./routes/cartRoutes.js";
import sellerRoutes from "./routes/sellerRoutes.js";
import sellerOrderRoutes from "./routes/sellerOrderRoutes.js";
import referralRoutes from "./routes/referralRoutes.js";
import paymentRoutes from "./routes/paymentRoutes.js";
import referralCommissionRoutes from "./routes/referralCommissionRoutes.js";
import referralCommissionAvailabilityRoutes from "./routes/referralCommissionAvailabilityRoutes.js";
import withdrawalRoutes from "./routes/withdrawalRoutes.js";
import walletTransactionRoutes from "./routes/walletTransactionRoutes.js";
import revenueRoutes from "./routes/revenueRoutes.js";
import premiumRoutes from "./routes/premiumRoutes.js";


// =========================
// Services
// =========================

import referralService from "./services/referralService.js";

// =========================
// App
// =========================

const app = express();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// =========================
// Middleware
// =========================

app.use(cors());

app.use(
  express.json({
    limit: "50mb",
  })
);

app.use(
  express.urlencoded({
    extended: true,
    limit: "50mb",
  })
);

app.use(
  "/uploads",
  express.static(
    path.join(__dirname, "uploads")
  )
);

// =========================
// Routes
// =========================

app.use(
  "/api/users",
  userRoutes
);

app.use(
  "/api/marketplace",
  marketplaceRoutes
);

app.use(
  "/api/orders",
  orderRoutes
);

app.use(
  "/api/wishlist",
  wishlistRoutes
);

app.use(
  "/api/cart",
  cartRoutes
);

app.use(
  "/api/seller",
  sellerRoutes
);

app.use(
  "/api/seller/orders",
  sellerOrderRoutes
);

// Referral routes
app.use(
  "/api/referrals",
  referralRoutes
);
app.use(
  "/api/revenue",
  revenueRoutes
);

// Referral commission routes
app.use(
  "/api/referral-commissions",
  referralCommissionRoutes
);

// Wallet routes
app.use(
  "/api/wallet",
  walletRoutes
);

// Payment routes
app.use(
  "/api/payments",
  paymentRoutes
);
app.use(
  "/api/premium",
  premiumRoutes
);

// Referral commission availability
app.use(
  "/api/referral-commission-availability",
  referralCommissionAvailabilityRoutes
);

app.use(
  "/api/withdrawals",
  withdrawalRoutes
);
app.use(
  "/api/wallet-transactions",
  walletTransactionRoutes
);
// =========================
// Test Route
// =========================

app.get("/test", (req, res) => {
  res.json({
    message: "App is working!",
  });
});

// =========================
// Home Route
// =========================

app.get("/", (req, res) => {
  res.send(
    "🚀 MUHUZE Global Link Backend is Running!"
  );
});

// =====================================================
// TEST: REFERRAL LEVELS
// =====================================================

app.get(
  "/test/referral-levels/:userId",
  async (req, res) => {
    try {
      const levels =
        await referralService.getReferralLevels(
          req.params.userId
        );

      res.json({
        success: true,
        userId: req.params.userId,
        levels,
      });
    } catch (error) {
      console.error(
        "Referral levels test error:",
        error
      );

      res.status(500).json({
        success: false,
        message: error.message,
      });
    }
  }
);

// =====================================================
// TEST: CREATE REVENUE + REFERRAL COMMISSIONS
// =====================================================

app.post(
  "/test/referral-commissions",
  async (req, res) => {
    try {
      const RevenueTransaction =
        (
          await import(
            "./models/RevenueTransaction.js"
          )
        ).default;

      const userId =
        "6a7d01a93ebf998b599ef584";

      // ==========================================
      // CREATE TEST REVENUE TRANSACTION
      // ==========================================

      const revenueTransaction =
        await RevenueTransaction.create({
          userId,

          sourceId:
            new mongoose.Types.ObjectId(),

          sourceType:
            "PRODUCT_SALE",

          sourceAmount:
            100,

          sourceCurrency:
            "USD",

          exchangeRate:
            1,

          accountingAmount:
            100,

          accountingCurrency:
            "USD",

          revenueRate:
            100,

          revenueAmount:
            100,

          referralEligible:
            true,

          status:
            "Completed",

          availableAt:
            new Date(),
        });

      // ==========================================
      // CREATE REFERRAL COMMISSIONS
      // ==========================================

      const commissions =
        await referralService.createCommissionsFromRevenue(
          revenueTransaction,
          new Date()
        );

      // ==========================================
      // RESPONSE
      // ==========================================

      res.json({
        success: true,
        revenueTransaction,
        commissions,
      });
    } catch (error) {
      console.error(
        "Referral commission test error:",
        error
      );

      res.status(500).json({
        success: false,
        message:
          error.message,
      });
    }
  }
);

// =========================
// Export
// =========================

export default app;