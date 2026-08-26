import express from "express";

import controller from "../controllers/referralCommissionAvailabilityController.js";

const router = express.Router();

/**
 * ==========================================
 * PROCESS ALL AVAILABLE COMMISSIONS
 * ==========================================
 */
router.post(
  "/process",
  controller.processAvailable
);

/**
 * ==========================================
 * MAKE ONE COMMISSION AVAILABLE
 * ==========================================
 */
router.post(
  "/:commissionId",
  controller.makeAvailable
);

export default router;