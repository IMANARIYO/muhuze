import express from "express";

import walletTransactionController from "../controllers/walletTransactionController.js";

import protect from "../middleware/authMiddleware.js";
import adminOnly from "../middleware/adminMiddleware.js";

const router = express.Router();

/**
 * ==========================================
 * GET ALL TRANSACTIONS — ADMIN
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/admin/all
 *
 * Admin only.
 */

router.get(
  "/admin/all",
  protect,
  adminOnly,
  walletTransactionController.getAllTransactions
);

/**
 * ==========================================
 * GET USER TRANSACTIONS
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/:userId
 *
 * Authenticated users.
 */

router.get(
  "/:userId",
  protect,
  walletTransactionController.getUserTransactions
);

/**
 * ==========================================
 * GET ONE TRANSACTION
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/transaction/:transactionId
 *
 * Authenticated users.
 */

router.get(
  "/transaction/:transactionId",
  protect,
  walletTransactionController.getTransaction
);

export default router;