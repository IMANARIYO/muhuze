import paymentService from "../services/paymentService.js";

/**
 * Create Payment
 */
const createPayment = async (req, res) => {
  try {
    const payment = await paymentService.createPayment(req.body);

    res.status(201).json({
      success: true,
      message: "Payment created successfully.",
      data: payment,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
/**
 * ==========================================
 * CHECK LIVE PAYMENT STATUS
 * ==========================================
 */

const checkPaymentStatus = async (
  req,
  res
) => {
  try {
    const payment =
      await paymentService.checkPaymentStatus(
        req.params.id
      );

    return res.json({
      success: true,

      message:
        "Payment status checked successfully.",

      data: payment,
    });
  } catch (error) {
    console.error(
      "Check payment status error:",
      error
    );

    return res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to check payment status.",
    });
  }
};
/**
 * Get Payment By ID
 */
const getPaymentById = async (req, res) => {
  try {
    const payment = await paymentService.getPaymentById(
      req.params.id
    );

    if (!payment) {
      return res.status(404).json({
        success: false,
        message: "Payment not found.",
      });
    }

    res.json({
      success: true,
      data: payment,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get User Payments
 */
const getUserPayments = async (req, res) => {
  try {
    const payments = await paymentService.getUserPayments(
      req.params.userId
    );

    res.json({
      success: true,
      count: payments.length,
      data: payments,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * NOWPayments IPN
 *
 * Receives payment-status notifications
 * from NOWPayments.
 */
const handleNowPaymentsIPN = async (req, res) => {
  try {
    // Diagnostic logs
    console.log("🔔 NOWPayments IPN RECEIVED");
    console.log("Payment ID:", req.body.payment_id);
    console.log("Payment Status:", req.body.payment_status);

    const signature =
      req.headers["x-nowpayments-sig"];

    const payment =
      await paymentService.processNowPaymentsIPN(
        req.body,
        signature
      );

    res.status(200).json({
      success: true,
      message: "IPN processed successfully.",
      data: payment,
    });
  } catch (error) {
    console.error(
      "NOWPayments IPN error:",
      error.message
    );

    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * IMPORTANT:
 * paymentRoutes.js imports this file
 * as a default import.
 */
export default {
  createPayment,
  getPaymentById,
  getUserPayments,
  handleNowPaymentsIPN,
  checkPaymentStatus,
};