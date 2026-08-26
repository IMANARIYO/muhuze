import referralService from "../services/referralService.js";

/**
 * Get all referrals belonging to a user.
 */
const getUserReferrals = async (req, res) => {
  try {
    const { referrerId } = req.params;

    const referrals =
      await referralService.getUserReferrals(
        referrerId
      );

    res.json({
      success: true,
      count: referrals.length,
      data: referrals,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get one referral.
 */
const getReferral = async (req, res) => {
  try {
    const {
      referrerId,
      referralId,
    } = req.params;

    const referral =
      await referralService.getReferral(
        referrerId,
        referralId
      );

    if (!referral) {
      return res.status(404).json({
        success: false,
        message: "Referral not found.",
      });
    }

    res.json({
      success: true,
      data: referral,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Create a referral.
 */
const createReferral = async (req, res) => {
  try {
    const referral =
      await referralService.createReferral(
        req.body
      );

    res.status(201).json({
      success: true,
      message:
        "Referral created successfully.",
      data: referral,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Update referral status.
 */
const updateReferralStatus = async (
  req,
  res
) => {
  try {
    const {
      referrerId,
      referralId,
    } = req.params;

    const { status } = req.body;

    if (!status) {
      return res.status(400).json({
        success: false,
        message: "Status is required.",
      });
    }

    const referral =
      await referralService.updateReferralStatus(
        referrerId,
        referralId,
        status
      );

    if (!referral) {
      return res.status(404).json({
        success: false,
        message: "Referral not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Referral status updated successfully.",
      data: referral,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get total referral rewards.
 */
const getTotalRewards = async (
  req,
  res
) => {
  try {
    const { referrerId } = req.params;

    const totalRewards =
      await referralService.getTotalRewards(
        referrerId
      );

    res.json({
      success: true,
      data: {
        totalRewards,
      },
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getUserReferrals,
  getReferral,
  createReferral,
  updateReferralStatus,
  getTotalRewards,
};