import express from "express";

import walletController from "../controllers/walletController.js";

import protect from "../middleware/authMiddleware.js";

const router = express.Router();

/**
 * Get current user's wallet
 */
router.get(
  "/",
  protect,
  walletController.getWallet
);

/**
 * Get current user's wallet transactions
 */
router.get(
  "/transactions",
  protect,
  walletController.getWalletTransactions
);

export default router;