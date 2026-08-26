import express from "express";

import withdrawalController from "../controllers/withdrawalController.js";

import protect from "../middleware/authMiddleware.js";
import adminOnly from "../middleware/adminMiddleware.js";

const router = express.Router();

/**
 * ==========================================
 * CREATE WITHDRAWAL
 * ==========================================
 *
 * POST
 * /api/withdrawals
 *
 * Authenticated users only.
 */

router.post(
  "/",
  protect,
  withdrawalController.createWithdrawal
);

/**
 * ==========================================
 * ADMIN
 * GET ALL WITHDRAWALS
 * ==========================================
 *
 * GET
 * /api/withdrawals/admin/all
 *
 * IMPORTANT:
 * This route MUST come before /:userId
 * so "admin" is not interpreted as a userId.
 */

router.get(
  "/admin/all",
  protect,
  adminOnly,
  withdrawalController.getAllWithdrawals
);

/**
 * ==========================================
 * PROCESS WITHDRAWAL
 * ==========================================
 *
 * POST
 * /api/withdrawals/:withdrawalId/process
 *
 * ADMIN ONLY
 */

router.post(
  "/:withdrawalId/process",
  protect,
  adminOnly,
  withdrawalController.processWithdrawal
);

/**
 * ==========================================
 * COMPLETE WITHDRAWAL
 * ==========================================
 *
 * POST
 * /api/withdrawals/:withdrawalId/complete
 *
 * ADMIN ONLY
 */

router.post(
  "/:withdrawalId/complete",
  protect,
  adminOnly,
  withdrawalController.completeWithdrawal
);

/**
 * ==========================================
 * REJECT WITHDRAWAL
 * ==========================================
 *
 * POST
 * /api/withdrawals/:withdrawalId/reject
 *
 * ADMIN ONLY
 */

router.post(
  "/:withdrawalId/reject",
  protect,
  adminOnly,
  withdrawalController.rejectWithdrawal
);

/**
 * ==========================================
 * GET USER WITHDRAWALS
 * ==========================================
 *
 * GET
 * /api/withdrawals/:userId
 *
 * Authenticated users.
 */

router.get(
  "/:userId",
  protect,
  withdrawalController.getUserWithdrawals
);

/**
 * ==========================================
 * GET ONE WITHDRAWAL
 * ==========================================
 *
 * GET
 * /api/withdrawals/:userId/:withdrawalId
 */

router.get(
  "/:userId/:withdrawalId",
  protect,
  withdrawalController.getWithdrawal
);

export default router;