import mongoose from "mongoose";

import Referral from "../models/Referral.js";
import ReferralCommission from "../models/ReferralCommission.js";
import RevenueTransaction from "../models/RevenueTransaction.js";
import walletService from "./walletService.js";

/**
 * ==========================================
 * COMMISSION LEVELS
 * ==========================================
 *
 * Level 1 = 12%
 * Level 2 = 5%
 * Level 3 = 3%
 *
 * Total = 20%
 */

const COMMISSION_RATES = {
  1: 0.12,
  2: 0.05,
  3: 0.03,
};

const REFERRAL_POOL_RATE = 0.20;

/**
 * ==========================================
 * PROCESS REFERRAL COMMISSIONS
 * ==========================================
 *
 * Takes one completed, referral-eligible
 * revenue transaction and creates the
 * referral commissions.
 *
 * IMPORTANT:
 *
 * Commissions are created as Pending.
 *
 * They are NOT added to the available
 * wallet balance immediately.
 *
 * The availability service will release
 * them when availableAt is reached.
 */

const processReferralCommissions = async (
  revenueTransactionId
) => {
  /**
   * ==========================================
   * VALIDATE REVENUE TRANSACTION ID
   * ==========================================
   */

  if (
    !mongoose.Types.ObjectId.isValid(
      revenueTransactionId
    )
  ) {
    throw new Error(
      "Invalid revenue transaction ID."
    );
  }

  /**
   * ==========================================
   * START DATABASE TRANSACTION
   * ==========================================
   */

  const session =
    await mongoose.startSession();

  try {
    let commissions = [];

    await session.withTransaction(
      async () => {
        /**
         * ==========================================
         * FIND REVENUE TRANSACTION
         * ==========================================
         */

        const revenueTransaction =
          await RevenueTransaction.findById(
            revenueTransactionId
          ).session(session);

        if (!revenueTransaction) {
          throw new Error(
            "Revenue transaction not found."
          );
        }

        /**
         * ==========================================
         * REVENUE MUST BE COMPLETED
         * ==========================================
         */

        if (
          revenueTransaction.status !==
          "Completed"
        ) {
          throw new Error(
            "Revenue transaction is not completed."
          );
        }

        /**
         * ==========================================
         * CHECK REFERRAL ELIGIBILITY
         * ==========================================
         */

        if (
          !revenueTransaction.referralEligible
        ) {
          return;
        }

        /**
         * ==========================================
         * PREVENT DUPLICATE COMMISSIONS
         * ==========================================
         */

        const existingCommission =
          await ReferralCommission.findOne({
            revenueTransaction:
              revenueTransaction._id,
          }).session(session);

        if (existingCommission) {
          return;
        }

        /**
         * ==========================================
         * CALCULATE REFERRAL POOL
         * ==========================================
         *
         * 20% of MUHUZE revenue.
         */

        const referralPoolAmount =
          Number(
            (
              revenueTransaction.revenueAmount *
              REFERRAL_POOL_RATE
            ).toFixed(2)
          );

        /**
         * ==========================================
         * FIND REFERRAL LEVELS
         * ==========================================
         */

        let currentUserId =
          revenueTransaction.userId;

        for (
          let level = 1;
          level <= 3;
          level++
        ) {
          /**
           * Find the person who referred
           * the current user.
           */

          const referral =
            await Referral.findOne({
              referredUser:
                currentUserId,

              status: {
                $in: [
                  "Pending",
                  "Completed",
                ],
              },
            }).session(session);

          /**
           * No more upline.
           */

          if (!referral) {
            break;
          }

          const referrerId =
            referral.referrer;

          /**
           * ==========================================
           * COMMISSION RATE
           * ==========================================
           */

          const commissionRate =
            COMMISSION_RATES[level];

          if (!commissionRate) {
            continue;
          }

          /**
           * ==========================================
           * COMMISSION AMOUNT
           * ==========================================
           *
           * The commission is calculated from
           * MUHUZE revenue, NOT from the customer's
           * full purchase amount.
           */

          const commissionAmount =
            Number(
              (
                revenueTransaction.revenueAmount *
                commissionRate
              ).toFixed(2)
            );

          /**
           * ==========================================
           * AVAILABLE DATE
           * ==========================================
           *
           * Product-sale commissions wait 7 days.
           *
           * Other revenue types can become available
           * according to their own timing.
           */

          let availableAt;

          if (
            revenueTransaction.sourceType ===
            "PRODUCT_SALE"
          ) {
            availableAt =
              new Date(
                Date.now() +
                  7 *
                    24 *
                    60 *
                    60 *
                    1000
              );
          } else {
            availableAt =
              new Date();
          }

          /**
           * ==========================================
           * CREATE PENDING COMMISSION
           * ==========================================
           */

          const createdCommissions =
            await ReferralCommission.create(
              [
                {
                  referrer:
                    referrerId,

                  referredUser:
                    revenueTransaction.userId,

                  revenueTransaction:
                    revenueTransaction._id,

                  sourceType:
                    revenueTransaction.sourceType,

                  level,

                  commissionRate:
                    commissionRate * 100,

                  revenueAmount:
                    revenueTransaction.revenueAmount,

                  referralPoolAmount,

                  commissionAmount,

                  currency:
                    revenueTransaction.accountingCurrency,

                  /**
                   * IMPORTANT:
                   * Do NOT make it Available here.
                   */

                  status:
                    "Pending",

                  availableAt,

                  description:
                    `Level ${level} referral commission.`,
                },
              ],
              {
                session,
              }
            );

          const commission =
            createdCommissions[0];

          commissions.push(
            commission
          );

          /**
           * ==========================================
           * ADD TO PENDING WALLET
           * ==========================================
           *
           * The money is NOT withdrawable yet.
           */

          await walletService.addPendingCommission(
            referrerId,
            commissionAmount,
            commission._id
          );

          /**
           * ==========================================
           * MOVE UP REFERRAL TREE
           * ==========================================
           */

          currentUserId =
            referrerId;
        }
      }
    );

    return commissions;
  } finally {
    await session.endSession();
  }
};

/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  processReferralCommissions,
};