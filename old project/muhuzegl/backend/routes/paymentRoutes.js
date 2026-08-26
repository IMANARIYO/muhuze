import express from "express";
import paymentController from "../controllers/paymentController.js";

const router = express.Router();

/**
 * Create a payment
 */
router.post(
  "/",
  paymentController.createPayment
);

/**
 * Check live NOWPayments status
 */
router.get(
  "/:id/status",
  paymentController.checkPaymentStatus
);

/**
 * Get one payment
 */
router.get(
  "/:id",
  paymentController.getPaymentById
);

/**
 * Get all payments belonging to a user
 */
router.get(
  "/user/:userId",
  paymentController.getUserPayments
);

/**
 * NOWPayments IPN webhook
 *
 * NOWPayments will call this endpoint
 * when the payment status changes.
 */
router.post(
  "/nowpayments/ipn",
  paymentController.handleNowPaymentsIPN
);

export default router;