import mongoose from "mongoose";

import referralCommissionAvailabilityService from "../services/referralCommissionAvailabilityService.js";

/**
 * ==========================================
 * MAKE ONE COMMISSION AVAILABLE
 * ==========================================
 */
const makeAvailable = async (req, res) => {
  try {
    const { commissionId } = req.params;

    // Validate MongoDB ID
    if (!mongoose.Types.ObjectId.isValid(commissionId)) {
      return res.status(400).json({
        success: false,
        message: "Invalid commission ID.",
      });
    }

    const commission =
      await referralCommissionAvailabilityService.makeAvailable(
        commissionId
      );

    res.status(200).json({
      success: true,
      message: "Commission is now available.",
      data: commission,
    });
  } catch (error) {
    console.error(
      "MAKE COMMISSION AVAILABLE ERROR:",
      error
    );

    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * ==========================================
 * PROCESS ALL AVAILABLE COMMISSIONS
 * ==========================================
 */
const processAvailable = async (req, res) => {
  try {
    const commissions =
      await referralCommissionAvailabilityService.processAvailableCommissions();

    res.status(200).json({
      success: true,
      count: commissions.length,
      data: commissions,
    });
  } catch (error) {
    console.error(
      "PROCESS AVAILABLE COMMISSIONS ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * ==========================================
 * EXPORT CONTROLLER
 * ==========================================
 */
export default {
  makeAvailable,
  processAvailable,
};