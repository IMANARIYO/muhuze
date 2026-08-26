import express from "express";

import referralCommissionController from "../controllers/referralCommissionController.js";
import protect from "../middleware/authMiddleware.js";

const router = express.Router();

/**
 * ==========================================
 * GET COMMISSION SUMMARY
 * ==========================================
 *
 * Only authenticated users.
 */
router.get(
  "/:referrerId/summary",
  protect,
  referralCommissionController.getCommissionSummary
);

/**
 * ==========================================
 * GET ALL COMMISSIONS
 * ==========================================
 *
 * Only authenticated users.
 */
router.get(
  "/:referrerId",
  protect,
  referralCommissionController.getUserCommissions
);

export default router;