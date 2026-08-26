import express from "express";

import revenueController from "../controllers/revenueController.js";

import protect from "../middleware/authMiddleware.js";
import adminOnly from "../middleware/adminMiddleware.js";

const router = express.Router();

/**
 * ==========================================
 * COMPLETE REVENUE — ADMIN
 * ==========================================
 */

router.post(
  "/:revenueTransactionId/complete",
  protect,
  adminOnly,
  revenueController.completeRevenueTransaction
);

export default router;