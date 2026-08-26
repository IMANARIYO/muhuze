import mongoose from "mongoose";
import ReferralCommission from "../models/ReferralCommission.js";

/**
 * ==========================================
 * GET ALL COMMISSIONS FOR A REFERRER
 * ==========================================
 */
const getUserCommissions = async (
  req,
  res
) => {
  try {
    const { referrerId } = req.params;

    if (
      !mongoose.Types.ObjectId.isValid(
        referrerId
      )
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid referrer ID.",
      });
    }

    const commissions =
      await ReferralCommission.find({
        referrer:
          new mongoose.Types.ObjectId(
            referrerId
          ),
      })
        .populate(
          "referredUser",
          "fullName email username"
        )
        .sort({
          createdAt: -1,
        });

    res.json({
      success: true,
      count: commissions.length,
      data: commissions,
    });
  } catch (error) {
    console.error(
      "GET USER COMMISSIONS ERROR:",
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
 * GET COMMISSION SUMMARY
 * ==========================================
 */
const getCommissionSummary = async (
  req,
  res
) => {
  try {
    const { referrerId } = req.params;

    if (
      !mongoose.Types.ObjectId.isValid(
        referrerId
      )
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid referrer ID.",
      });
    }

    const objectId =
      new mongoose.Types.ObjectId(
        referrerId
      );

    const result =
      await ReferralCommission.aggregate([
        {
          $match: {
            referrer: objectId,
          },
        },

        {
          $group: {
            _id: null,

            totalCommission: {
              $sum: "$commissionAmount",
            },

            pendingCommission: {
              $sum: {
                $cond: [
                  {
                    $eq: [
                      "$status",
                      "Pending",
                    ],
                  },
                  "$commissionAmount",
                  0,
                ],
              },
            },

            availableCommission: {
              $sum: {
                $cond: [
                  {
                    $eq: [
                      "$status",
                      "Available",
                    ],
                  },
                  "$commissionAmount",
                  0,
                ],
              },
            },

            reversedCommission: {
              $sum: {
                $cond: [
                  {
                    $eq: [
                      "$status",
                      "Reversed",
                    ],
                  },
                  "$commissionAmount",
                  0,
                ],
              },
            },

            cancelledCommission: {
              $sum: {
                $cond: [
                  {
                    $eq: [
                      "$status",
                      "Cancelled",
                    ],
                  },
                  "$commissionAmount",
                  0,
                ],
              },
            },
          },
        },
      ]);

    const summary =
      result[0] || {
        totalCommission: 0,
        pendingCommission: 0,
        availableCommission: 0,
        reversedCommission: 0,
        cancelledCommission: 0,
      };

    delete summary._id;

    res.json({
      success: true,
      data: summary,
    });
  } catch (error) {
    console.error(
      "GET COMMISSION SUMMARY ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getUserCommissions,
  getCommissionSummary,
};