import mongoose from "mongoose";

import WalletTransaction from "../models/WalletTransaction.js";

/**
 * ==========================================
 * GET ALL WALLET TRANSACTIONS — ADMIN
 * ==========================================
 */

const getAllTransactions = async () => {
  return await WalletTransaction.find()
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
 * GET USER TRANSACTIONS
 * ==========================================
 */

const getUserTransactions = async (
  userId
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

  return await WalletTransaction.find({
    userId,
  }).sort({
    createdAt: -1,
  });
};

/**
 * ==========================================
 * GET ONE TRANSACTION
 * ==========================================
 */

const getTransaction = async (
  transactionId
) => {
  if (
    !mongoose.Types.ObjectId.isValid(
      transactionId
    )
  ) {
    throw new Error(
      "Invalid transaction ID."
    );
  }

  return await WalletTransaction.findById(
    transactionId
  ).populate(
    "userId",
    "fullName email phone"
  );
};

/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  getAllTransactions,
  getUserTransactions,
  getTransaction,
};