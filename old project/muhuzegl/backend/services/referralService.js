import mongoose from "mongoose";

import Referral from "../models/Referral.js";
import User from "../models/User.js";

/**
 * ==========================================
 * REFERRAL SERVICE
 * ==========================================
 *
 * Handles:
 *
 * 1. Get all referrals for a referrer
 * 2. Get one referral
 * 3. Create referral
 * 4. Update referral status
 * 5. Calculate total referral rewards
 *
 * IMPORTANT:
 *
 * Referral records and referral commissions are
 * separate concepts.
 *
 * Referral
 *   ↓
 * Records who referred whom
 *
 * ReferralCommission
 *   ↓
 * Handles financial commissions generated
 * from eligible MUHUZE revenue.
 */

/**
 * ==========================================
 * GET USER REFERRALS
 * ==========================================
 *
 * Returns all users referred by referrerId.
 */
const getUserReferrals = async (
  referrerId
) => {
  /**
   * Validate MongoDB ID.
   */
  if (
    !mongoose.Types.ObjectId.isValid(
      referrerId
    )
  ) {
    throw new Error(
      "Invalid referrer ID."
    );
  }

  const referrals =
    await Referral.find({
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

  return referrals;
};

/**
 * ==========================================
 * GET ONE REFERRAL
 * ==========================================
 */
const getReferral = async (
  referrerId,
  referralId
) => {
  /**
   * Validate IDs.
   */
  if (
    !mongoose.Types.ObjectId.isValid(
      referrerId
    )
  ) {
    throw new Error(
      "Invalid referrer ID."
    );
  }

  if (
    !mongoose.Types.ObjectId.isValid(
      referralId
    )
  ) {
    throw new Error(
      "Invalid referral ID."
    );
  }

  /**
   * Make sure the referral belongs
   * to this referrer.
   */
  const referral =
    await Referral.findOne({
      _id: referralId,
      referrer: referrerId,
    })
      .populate(
        "referredUser",
        "fullName email username"
      )
      .populate(
        "referrer",
        "fullName email username"
      );

  return referral;
};

/**
 * ==========================================
 * CREATE REFERRAL
 * ==========================================
 *
 * Creates a referral relationship.
 *
 * Example:
 *
 * User A
 *   ↓ referral link
 * User B registers
 *
 * Referral:
 *
 * referrer     = User A
 * referredUser = User B
 * status       = Pending
 */
const createReferral = async (
  data
) => {
  const {
    referrer,
    referredUser,
    referralCode,
    reward,
    status,
  } = data;

  /**
   * ==========================================
   * VALIDATE REQUIRED FIELDS
   * ==========================================
   */

  if (!referrer) {
    throw new Error(
      "Referrer is required."
    );
  }

  if (!referredUser) {
    throw new Error(
      "Referred user is required."
    );
  }

  if (!referralCode) {
    throw new Error(
      "Referral code is required."
    );
  }

  /**
   * ==========================================
   * VALIDATE OBJECT IDS
   * ==========================================
   */

  if (
    !mongoose.Types.ObjectId.isValid(
      referrer
    )
  ) {
    throw new Error(
      "Invalid referrer ID."
    );
  }

  if (
    !mongoose.Types.ObjectId.isValid(
      referredUser
    )
  ) {
    throw new Error(
      "Invalid referred user ID."
    );
  }

  /**
   * ==========================================
   * PREVENT SELF-REFERRAL
   * ==========================================
   */

  if (
    referrer.toString() ===
    referredUser.toString()
  ) {
    throw new Error(
      "A user cannot refer themselves."
    );
  }

  /**
   * ==========================================
   * MAKE SURE USERS EXIST
   * ==========================================
   */

  const referrerUser =
    await User.findById(referrer);

  if (!referrerUser) {
    throw new Error(
      "Referrer user not found."
    );
  }

  const referredUserRecord =
    await User.findById(
      referredUser
    );

  if (!referredUserRecord) {
    throw new Error(
      "Referred user not found."
    );
  }

  /**
   * ==========================================
   * PREVENT DUPLICATE REFERRAL
   * ==========================================
   *
   * A user should normally have only one
   * referral relationship.
   */

  const existingReferral =
    await Referral.findOne({
      referredUser,
    });

  if (existingReferral) {
    throw new Error(
      "This user already has a referral relationship."
    );
  }

  /**
   * ==========================================
   * CREATE REFERRAL
   * ==========================================
   */

  const referral =
    await Referral.create({
      referrer,

      referredUser,

      referralCode:
        referralCode.trim(),

      /**
       * Keep the existing model default.
       *
       * If a reward is explicitly supplied,
       * use it.
       */
      reward:
        reward !== undefined
          ? reward
          : 2000,

      status:
        status || "Pending",
    });

  /**
   * Return populated referral.
   */

  return await Referral.findById(
    referral._id
  )
    .populate(
      "referredUser",
      "fullName email username"
    )
    .populate(
      "referrer",
      "fullName email username"
    );
};

/**
 * ==========================================
 * UPDATE REFERRAL STATUS
 * ==========================================
 */
const updateReferralStatus = async (
  referrerId,
  referralId,
  status
) => {
  /**
   * Validate IDs.
   */

  if (
    !mongoose.Types.ObjectId.isValid(
      referrerId
    )
  ) {
    throw new Error(
      "Invalid referrer ID."
    );
  }

  if (
    !mongoose.Types.ObjectId.isValid(
      referralId
    )
  ) {
    throw new Error(
      "Invalid referral ID."
    );
  }

  /**
   * Validate status.
   */

  if (
    !["Pending", "Completed"].includes(
      status
    )
  ) {
    throw new Error(
      "Invalid referral status."
    );
  }

  /**
   * Find referral belonging to
   * the specified referrer.
   */

  const referral =
    await Referral.findOne({
      _id: referralId,
      referrer: referrerId,
    });

  if (!referral) {
    return null;
  }

  /**
   * Update status.
   */

  referral.status = status;

  await referral.save();

  /**
   * Return populated result.
   */

  return await Referral.findById(
    referral._id
  )
    .populate(
      "referredUser",
      "fullName email username"
    )
    .populate(
      "referrer",
      "fullName email username"
    );
};

/**
 * ==========================================
 * GET TOTAL REFERRAL REWARDS
 * ==========================================
 *
 * Calculates the total reward recorded
 * on referrals belonging to a referrer.
 *
 * Only Completed referrals are counted.
 *
 * Example:
 *
 * Referral 1 = 2000
 * Referral 2 = 2000
 * Referral 3 = 2000
 *
 * Total = 6000
 */
const getTotalRewards = async (
  referrerId
) => {
  /**
   * Validate ID.
   */

  if (
    !mongoose.Types.ObjectId.isValid(
      referrerId
    )
  ) {
    throw new Error(
      "Invalid referrer ID."
    );
  }

  /**
   * Aggregate completed referral rewards.
   */

  const result =
    await Referral.aggregate([
      {
        $match: {
          referrer:
            new mongoose.Types.ObjectId(
              referrerId
            ),

          status:
            "Completed",
        },
      },

      {
        $group: {
          _id: null,

          totalRewards: {
            $sum: "$reward",
          },
        },
      },
    ]);

  /**
   * No completed referrals.
   */

  if (!result.length) {
    return 0;
  }

  return result[0].totalRewards || 0;
};

/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  getUserReferrals,

  getReferral,

  createReferral,

  updateReferralStatus,

  getTotalRewards,
};