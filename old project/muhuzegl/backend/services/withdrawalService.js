import mongoose from "mongoose";

import Wallet from "../models/Wallet.js";
import WalletTransaction from "../models/WalletTransaction.js";
import Withdrawal from "../models/Withdrawal.js";

import {
  WITHDRAWAL_FEE_RATE,
  WITHDRAWAL_FEE_PERCENT,
} from "../config/withdrawal.js";

/**
 * ==========================================
 * CREATE WITHDRAWAL
 * ==========================================
 */

const createWithdrawal = async ({
  userId,
  amount,
  paymentMethod,
  network,
  accountNumber,
  accountName,
}) => {
  if (
    !mongoose.Types.ObjectId.isValid(userId)
  ) {
    throw new Error("Invalid user ID.");
  }

  if (
    typeof amount !== "number" ||
    !Number.isFinite(amount) ||
    amount <= 0
  ) {
    throw new Error(
      "Withdrawal amount must be greater than zero."
    );
  }

  if (amount < 5) {
    throw new Error(
      "Minimum withdrawal amount is $5."
    );
  }

  /**
   * ==========================================
   * PAYMENT METHODS
   * ==========================================
   */

  const allowedMethods = [
    "MTN_MOBILE_MONEY",
    "AIRTEL_MONEY",
    "BANK_TRANSFER",
    "USDT",
    "USDC",
  ];

  if (
    !allowedMethods.includes(paymentMethod)
  ) {
    throw new Error(
      "Invalid payment method."
    );
  }

  /**
   * ==========================================
   * CRYPTO NETWORK
   * ==========================================
   */

  const cryptoMethods = [
    "USDT",
    "USDC",
  ];

  if (
    cryptoMethods.includes(paymentMethod)
  ) {
    if (!network) {
      throw new Error(
        "Crypto network is required."
      );
    }

    const allowedNetworks = [
      "TRC20",
      "ERC20",
      "BEP20",
      "POLYGON",
      "ARBITRUM",
      "SOLANA",
    ];

    if (
      !allowedNetworks.includes(network)
    ) {
      throw new Error(
        "Invalid crypto network."
      );
    }
  } else {
    network = undefined;
  }

  /**
   * ==========================================
   * PAYMENT ACCOUNT
   * ==========================================
   */

  if (!accountNumber?.trim()) {
    throw new Error(
      "Payment account is required."
    );
  }

  /**
   * ==========================================
   * CALCULATE WITHDRAWAL FEE
   * ==========================================
   */

  const feeAmount = Number(
    (
      amount * WITHDRAWAL_FEE_RATE
    ).toFixed(2)
  );

  const netAmount = Number(
    (
      amount - feeAmount
    ).toFixed(2)
  );

  if (netAmount <= 0) {
    throw new Error(
      "Withdrawal amount is too small after fees."
    );
  }

  /**
   * ==========================================
   * DATABASE TRANSACTION
   * ==========================================
   */

  const session =
    await mongoose.startSession();

  try {
    let withdrawal;

    await session.withTransaction(
      async () => {
        /**
         * ==========================================
         * FIND USER WALLET
         * ==========================================
         */

        const wallet =
          await Wallet.findOne({
            userId,
          }).session(session);

        if (!wallet) {
          throw new Error(
            "Wallet not found."
          );
        }

        /**
         * ==========================================
         * WEEKLY WITHDRAWAL LIMIT
         * ==========================================
         */

        const oneWeekAgo =
          new Date(
            Date.now() -
              7 * 24 * 60 * 60 * 1000
          );

        const recentWithdrawal =
          await Withdrawal.findOne({
            userId,

            createdAt: {
              $gte: oneWeekAgo,
            },

            status: {
              $in: [
                "Pending",
                "Processing",
                "Completed",
              ],
            },
          }).session(session);

        if (recentWithdrawal) {
          throw new Error(
            "You can only make one withdrawal per week."
          );
        }

        /**
         * ==========================================
         * WALLET STATUS
         * ==========================================
         */

        if (
          wallet.status !== "Active"
        ) {
          throw new Error(
            "Wallet is not active."
          );
        }

        /**
         * ==========================================
         * BALANCE CHECK
         * ==========================================
         */

        if (
          wallet.balance < amount
        ) {
          throw new Error(
            "Insufficient wallet balance."
          );
        }

        /**
         * ==========================================
         * RESERVE FULL REQUESTED AMOUNT
         * ==========================================
         */

        wallet.balance -= amount;

        await wallet.save({
          session,
        });

        /**
         * ==========================================
         * CREATE WITHDRAWAL
         * ==========================================
         */

        const createdWithdrawals =
          await Withdrawal.create(
            [
              {
                userId,

                requestedAmount:
                  amount,

                feeRate:
                  WITHDRAWAL_FEE_PERCENT,

                feeAmount,

                netAmount,

                currency:
                  wallet.currency,

                paymentMethod,

                network,

                accountNumber:
                  accountNumber.trim(),

                accountName:
                  accountName?.trim(),

                status: "Pending",

                description:
                  "Wallet withdrawal request.",
              },
            ],
            {
              session,
            }
          );

        withdrawal =
          createdWithdrawals[0];

        /**
         * ==========================================
         * CREATE WALLET TRANSACTION
         * ==========================================
         */

        const walletTransactions =
          await WalletTransaction.create(
            [
              {
                userId,

                type:
                  "WITHDRAWAL",

                amount:
                  -amount,

                currency:
                  wallet.currency,

                referenceId:
                  withdrawal._id,

                referenceType:
                  "Withdrawal",

                status:
                  "Pending",

                description:
                  `Withdrawal request. Fee: ${feeAmount} ${wallet.currency}.`,
              },
            ],
            {
              session,
            }
          );

        /**
         * ==========================================
         * CONNECT TRANSACTION
         * ==========================================
         */

        withdrawal.walletTransactionId =
          walletTransactions[0]._id;

        await withdrawal.save({
          session,
        });
      }
    );

    return withdrawal;
  } finally {
    await session.endSession();
  }
};

/**
 * ==========================================
 * PROCESS WITHDRAWAL
 * ==========================================
 *
 * Pending → Processing
 */

const processWithdrawal = async (
  withdrawalId,
  processedBy
) => {
  if (
    !mongoose.Types.ObjectId.isValid(
      withdrawalId
    )
  ) {
    throw new Error(
      "Invalid withdrawal ID."
    );
  }

  if (
    processedBy &&
    !mongoose.Types.ObjectId.isValid(
      processedBy
    )
  ) {
    throw new Error(
      "Invalid processor ID."
    );
  }

  const session =
    await mongoose.startSession();

  try {
    let withdrawal;

    await session.withTransaction(
      async () => {
        withdrawal =
          await Withdrawal.findById(
            withdrawalId
          ).session(session);

        if (!withdrawal) {
          throw new Error(
            "Withdrawal not found."
          );
        }

        if (
          withdrawal.status !==
          "Pending"
        ) {
          throw new Error(
            `Withdrawal cannot be processed because it is ${withdrawal.status}.`
          );
        }

        withdrawal.status =
          "Processing";

        if (processedBy) {
          withdrawal.processedBy =
            processedBy;
        }

        await withdrawal.save({
          session,
        });
      }
    );

    return withdrawal;
  } finally {
    await session.endSession();
  }
};

/**
 * ==========================================
 * COMPLETE WITHDRAWAL
 * ==========================================
 *
 * Processing → Completed
 */

const completeWithdrawal = async (
  withdrawalId,
  processedBy
) => {
  if (
    !mongoose.Types.ObjectId.isValid(
      withdrawalId
    )
  ) {
    throw new Error(
      "Invalid withdrawal ID."
    );
  }

  if (
    processedBy &&
    !mongoose.Types.ObjectId.isValid(
      processedBy
    )
  ) {
    throw new Error(
      "Invalid processor ID."
    );
  }

  const session =
    await mongoose.startSession();

  try {
    let withdrawal;

    await session.withTransaction(
      async () => {
        withdrawal =
          await Withdrawal.findById(
            withdrawalId
          ).session(session);

        if (!withdrawal) {
          throw new Error(
            "Withdrawal not found."
          );
        }

        if (
          withdrawal.status !==
          "Processing"
        ) {
          throw new Error(
            `Withdrawal cannot be completed because it is ${withdrawal.status}.`
          );
        }

        /**
         * ==========================================
         * FIND WALLET
         * ==========================================
         */

        const wallet =
          await Wallet.findOne({
            userId:
              withdrawal.userId,
          }).session(session);

        if (!wallet) {
          throw new Error(
            "Wallet not found."
          );
        }

        /**
         * ==========================================
         * UPDATE TOTAL WITHDRAWN
         * ==========================================
         */

        wallet.totalWithdrawn +=
          withdrawal.requestedAmount;

        await wallet.save({
          session,
        });

        /**
         * ==========================================
         * UPDATE WALLET TRANSACTION
         * ==========================================
         */

        const walletTransaction =
          await WalletTransaction.findById(
            withdrawal.walletTransactionId
          ).session(session);

        if (
          !walletTransaction
        ) {
          throw new Error(
            "Wallet transaction not found."
          );
        }

        walletTransaction.status =
          "Completed";

        walletTransaction.description =
          `Withdrawal completed. Fee: ${withdrawal.feeAmount} ${withdrawal.currency}. Net payout: ${withdrawal.netAmount} ${withdrawal.currency}.`;

        await walletTransaction.save({
          session,
        });

        /**
         * ==========================================
         * COMPLETE WITHDRAWAL
         * ==========================================
         */

        withdrawal.status =
          "Completed";

        withdrawal.processedAt =
          new Date();

        if (processedBy) {
          withdrawal.processedBy =
            processedBy;
        }

        await withdrawal.save({
          session,
        });
      }
    );

    return withdrawal;
  } finally {
    await session.endSession();
  }
};

/**
 * ==========================================
 * REJECT WITHDRAWAL
 * ==========================================
 *
 * Pending / Processing → Rejected
 *
 * The reserved requested amount is
 * returned to the user's wallet.
 *
 * IMPORTANT:
 *
 * We also create a separate REFUND
 * wallet transaction so the financial
 * history clearly shows the money returning.
 */

const rejectWithdrawal = async (
  withdrawalId,
  rejectionReason,
  processedBy
) => {
  if (
    !mongoose.Types.ObjectId.isValid(
      withdrawalId
    )
  ) {
    throw new Error(
      "Invalid withdrawal ID."
    );
  }

  if (
    !rejectionReason?.trim()
  ) {
    throw new Error(
      "Rejection reason is required."
    );
  }

  if (
    processedBy &&
    !mongoose.Types.ObjectId.isValid(
      processedBy
    )
  ) {
    throw new Error(
      "Invalid processor ID."
    );
  }

  const session =
    await mongoose.startSession();

  try {
    let withdrawal;

    await session.withTransaction(
      async () => {
        /**
         * ==========================================
         * FIND WITHDRAWAL
         * ==========================================
         */

        withdrawal =
          await Withdrawal.findById(
            withdrawalId
          ).session(session);

        if (!withdrawal) {
          throw new Error(
            "Withdrawal not found."
          );
        }

        /**
         * ==========================================
         * ONLY PENDING / PROCESSING
         * ==========================================
         */

        if (
          withdrawal.status !==
            "Pending" &&
          withdrawal.status !==
            "Processing"
        ) {
          throw new Error(
            `Withdrawal cannot be rejected because it is ${withdrawal.status}.`
          );
        }

        /**
         * ==========================================
         * FIND WALLET
         * ==========================================
         */

        const wallet =
          await Wallet.findOne({
            userId:
              withdrawal.userId,
          }).session(session);

        if (!wallet) {
          throw new Error(
            "Wallet not found."
          );
        }

        /**
         * ==========================================
         * PREVENT DUPLICATE REFUND
         * ==========================================
         *
         * This protects the wallet if the
         * rejection operation is accidentally
         * attempted more than once.
         */

        const existingRefund =
          await WalletTransaction.findOne({
            userId:
              withdrawal.userId,

            type:
              "REFUND",

            amount:
              withdrawal.requestedAmount,

            referenceId:
              withdrawal._id,

            referenceType:
              "Withdrawal",

            status:
              "Completed",
          }).session(session);

        /**
         * ==========================================
         * RETURN RESERVED MONEY
         * ==========================================
         */

        if (!existingRefund) {
          wallet.balance +=
            withdrawal.requestedAmount;

          await wallet.save({
            session,
          });
        }

        /**
         * ==========================================
         * CANCEL ORIGINAL WITHDRAWAL TRANSACTION
         * ==========================================
         */

        const walletTransaction =
          await WalletTransaction.findById(
            withdrawal.walletTransactionId
          ).session(session);

        if (
          !walletTransaction
        ) {
          throw new Error(
            "Wallet transaction not found."
          );
        }

        walletTransaction.status =
          "Cancelled";

        walletTransaction.description =
          `Withdrawal rejected. ${rejectionReason.trim()}`;

        await walletTransaction.save({
          session,
        });

        /**
         * ==========================================
         * CREATE REFUND TRANSACTION
         * ==========================================
         *
         * Positive amount means money
         * was returned to the wallet.
         */

        if (!existingRefund) {
          await WalletTransaction.create(
            [
              {
                userId:
                  withdrawal.userId,

                type:
                  "REFUND",

                amount:
                  withdrawal.requestedAmount,

                currency:
                  withdrawal.currency,

                referenceId:
                  withdrawal._id,

                referenceType:
                  "Withdrawal",

                status:
                  "Completed",

                description:
                  `Withdrawal refund. ${rejectionReason.trim()}`,
              },
            ],
            {
              session,
            }
          );
        }

        /**
         * ==========================================
         * UPDATE WITHDRAWAL
         * ==========================================
         */

        withdrawal.status =
          "Rejected";

        withdrawal.rejectionReason =
          rejectionReason.trim();

        withdrawal.processedAt =
          new Date();

        if (processedBy) {
          withdrawal.processedBy =
            processedBy;
        }

        await withdrawal.save({
          session,
        });
      }
    );

    return withdrawal;
  } finally {
    await session.endSession();
  }
};

/**
 * ==========================================
 * GET USER WITHDRAWALS
 * ==========================================
 */

const getUserWithdrawals =
  async (userId) => {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid user ID."
      );
    }

    return await Withdrawal.find({
      userId,
    }).sort({
      createdAt: -1,
    });
  };

/**
 * ==========================================
 * GET ONE WITHDRAWAL
 * ==========================================
 */

const getWithdrawal = async (
  userId,
  withdrawalId
) => {
  if (
    !mongoose.Types.ObjectId.isValid(
      userId
    )
  ) {
    throw new Error(
      "Invalid user ID."
    );
  }

  if (
    !mongoose.Types.ObjectId.isValid(
      withdrawalId
    )
  ) {
    throw new Error(
      "Invalid withdrawal ID."
    );
  }

  return await Withdrawal.findOne({
    _id: withdrawalId,
    userId,
  });
};

/**
 * ==========================================
 * GET ALL WITHDRAWALS — ADMIN
 * ==========================================
 */

const getAllWithdrawals =
  async () => {
    return await Withdrawal.find()
      .populate(
        "userId",
        "fullName email phone"
      )
      .sort({
        createdAt: -1,
      });
  };

/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  createWithdrawal,
  processWithdrawal,
  completeWithdrawal,
  rejectWithdrawal,
  getUserWithdrawals,
  getWithdrawal,
  getAllWithdrawals,
};