import express from "express";

import premiumController from "../controllers/premiumController.js";
import protect from "../middleware/authMiddleware.js";

const router = express.Router();

/**
 * ==========================================
 * CREATE PREMIUM SUBSCRIPTION
 * ==========================================
 */
router.post(
  "/",
  protect,
  premiumController.createPremiumSubscription
);

/**
 * ==========================================
 * CANCEL PENDING PREMIUM PAYMENT
 * ==========================================
 */
router.post(
  "/pending/cancel",
  protect,
  premiumController.cancelPendingPremium
);

/**
 * ==========================================
 * GET CURRENT PREMIUM SUBSCRIPTION
 * ==========================================
 */
router.get(
  "/me",
  protect,
  premiumController.getMyPremiumSubscription
);

/**
 * ==========================================
 * GET PREMIUM HISTORY
 * ==========================================
 */
router.get(
  "/history",
  protect,
  premiumController.getPremiumHistory
);

export default router;