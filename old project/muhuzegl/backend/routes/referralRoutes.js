import express from "express";

import referralController from "../controllers/referralController.js";
import protect from "../middleware/authMiddleware.js";

const router = express.Router();

/*
 * Create a referral
 *
 * Referrals should normally be created
 * automatically during registration.
 *
 * Keep this protected in case this endpoint
 * is used manually.
 */
router.post(
  "/",
  protect,
  referralController.createReferral
);

/*
 * Get total referral rewards
 */
router.get(
  "/:referrerId/rewards",
  protect,
  referralController.getTotalRewards
);

/*
 * Get one referral
 */
router.get(
  "/:referrerId/:referralId",
  protect,
  referralController.getReferral
);

/*
 * Update referral status
 */
router.put(
  "/:referrerId/:referralId/status",
  protect,
  referralController.updateReferralStatus
);

/*
 * Get all referrals belonging to a user
 */
router.get(
  "/:referrerId",
  protect,
  referralController.getUserReferrals
);

export default router;