import mongoose from "mongoose";

import walletTransactionService from "../services/walletTransactionService.js";

/**
 * ==========================================
 * GET ALL TRANSACTIONS — ADMIN
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/admin/all
 */

const getAllTransactions = async (
  req,
  res
) => {
  try {
    const transactions =
      await walletTransactionService.getAllTransactions();

    res.status(200).json({
      success: true,
      count: transactions.length,
      data: transactions,
    });
  } catch (error) {
    console.error(
      "GET ALL TRANSACTIONS ERROR:",
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
 * GET USER TRANSACTIONS
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/:userId
 */

const getUserTransactions = async (
  req,
  res
) => {
  try {
    const { userId } = req.params;

    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid user ID.",
      });
    }

    const transactions =
      await walletTransactionService.getUserTransactions(
        userId
      );

    res.status(200).json({
      success: true,
      count: transactions.length,
      data: transactions,
    });
  } catch (error) {
    console.error(
      "GET USER TRANSACTIONS ERROR:",
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
 * GET ONE TRANSACTION
 * ==========================================
 *
 * GET
 * /api/wallet-transactions/transaction/:transactionId
 */

const getTransaction = async (
  req,
  res
) => {
  try {
    const { transactionId } =
      req.params;

    if (
      !mongoose.Types.ObjectId.isValid(
        transactionId
      )
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid transaction ID.",
      });
    }

    const transaction =
      await walletTransactionService.getTransaction(
        transactionId
      );

    if (!transaction) {
      return res.status(404).json({
        success: false,
        message:
          "Transaction not found.",
      });
    }

    res.status(200).json({
      success: true,
      data: transaction,
    });
  } catch (error) {
    console.error(
      "GET TRANSACTION ERROR:",
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
 * EXPORT
 * ==========================================
 */

export default {
  getAllTransactions,
  getUserTransactions,
  getTransaction,
};