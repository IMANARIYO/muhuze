import mongoose from "mongoose";

import revenueService from "../services/revenueService.js";

/**
 * ==========================================
 * COMPLETE REVENUE TRANSACTION
 * ==========================================
 *
 * POST
 * /api/revenue/:revenueTransactionId/complete
 */

const completeRevenueTransaction = async (
  req,
  res
) => {
  try {
    const {
      revenueTransactionId,
    } = req.params;

    if (
      !mongoose.Types.ObjectId.isValid(
        revenueTransactionId
      )
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid revenue transaction ID.",
      });
    }

    const revenueTransaction =
      await revenueService.completeRevenueTransaction(
        revenueTransactionId
      );

    res.status(200).json({
      success: true,
      message:
        "Revenue transaction completed successfully.",
      data: revenueTransaction,
    });
  } catch (error) {
    console.error(
      "COMPLETE REVENUE ERROR:",
      error
    );

    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  completeRevenueTransaction,
};