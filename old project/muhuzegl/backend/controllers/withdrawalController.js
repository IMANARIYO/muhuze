import mongoose from "mongoose";

import withdrawalService from "../services/withdrawalService.js";

/**
 * ==========================================
 * CREATE WITHDRAWAL
 * ==========================================
 *
 * POST
 * /api/withdrawals
 *
 * Authenticated users only.
 *
 * IMPORTANT:
 * The user ID comes from the authenticated
 * JWT, NOT from req.body.
 */

const createWithdrawal = async (
  req,
  res
) => {
  try {
    const {
      amount,
      paymentMethod,
      network,
      accountNumber,
      accountName,
    } = req.body;

    /**
     * Get the authenticated user.
     */

    const userId = req.user._id;

    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid authenticated user.",
      });
    }

    /**
     * Validate amount.
     */

    const withdrawalAmount =
      Number(amount);

    if (
      !Number.isFinite(
        withdrawalAmount
      ) ||
      withdrawalAmount <= 0
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Withdrawal amount must be greater than zero.",
      });
    }

    /**
     * Create withdrawal.
     */

    const withdrawal =
      await withdrawalService.createWithdrawal({
        userId,

        amount:
          withdrawalAmount,

        paymentMethod,

        network,

        accountNumber,

        accountName,
      });

    res.status(201).json({
      success: true,

      message:
        "Withdrawal request created successfully.",

      data: withdrawal,
    });

  } catch (error) {

    console.error(
      "CREATE WITHDRAWAL ERROR:",
      error
    );

    res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to create withdrawal.",
    });
  }
};

/**
 * ==========================================
 * GET CURRENT USER WITHDRAWALS
 * ==========================================
 *
 * GET
 * /api/withdrawals/:userId
 *
 * IMPORTANT:
 * The authenticated user can only access
 * their own withdrawal history.
 */

const getUserWithdrawals = async (
  req,
  res
) => {
  try {

    const requestedUserId =
      req.params.userId;

    const authenticatedUserId =
      req.user._id.toString();

    /**
     * Prevent users from accessing
     * another user's withdrawals.
     */

    if (
      requestedUserId !==
      authenticatedUserId
    ) {
      return res.status(403).json({
        success: false,
        message:
          "You are not authorized to view these withdrawals.",
      });
    }

    if (
      !mongoose.Types.ObjectId.isValid(
        requestedUserId
      )
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid user ID.",
      });
    }

    const withdrawals =
      await withdrawalService.getUserWithdrawals(
        requestedUserId
      );

    res.json({
      success: true,

      count:
        withdrawals.length,

      data:
        withdrawals,
    });

  } catch (error) {

    console.error(
      "GET USER WITHDRAWALS ERROR:",
      error
    );

    res.status(500).json({
      success: false,

      message:
        error.message ||
        "Unable to load withdrawals.",
    });
  }
};

/**
 * ==========================================
 * GET ONE WITHDRAWAL
 * ==========================================
 *
 * GET
 * /api/withdrawals/:userId/:withdrawalId
 *
 * Authenticated users can only access
 * their own withdrawal.
 */

const getWithdrawal = async (
  req,
  res
) => {
  try {

    const {
      userId,
      withdrawalId,
    } = req.params;

    const authenticatedUserId =
      req.user._id.toString();

    /**
     * Ownership check.
     */

    if (
      userId !==
      authenticatedUserId
    ) {
      return res.status(403).json({
        success: false,
        message:
          "You are not authorized to view this withdrawal.",
      });
    }

    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid user ID.",
      });
    }

    if (
      !mongoose.Types.ObjectId.isValid(
        withdrawalId
      )
    ) {
      return res.status(400).json({
        success: false,
        message:
          "Invalid withdrawal ID.",
      });
    }

    const withdrawal =
      await withdrawalService.getWithdrawal(
        userId,
        withdrawalId
      );

    if (!withdrawal) {
      return res.status(404).json({
        success: false,
        message:
          "Withdrawal not found.",
      });
    }

    res.json({
      success: true,

      data:
        withdrawal,
    });

  } catch (error) {

    console.error(
      "GET WITHDRAWAL ERROR:",
      error
    );

    res.status(500).json({
      success: false,

      message:
        error.message ||
        "Unable to load withdrawal.",
    });
  }
};

/**
 * ==========================================
 * PROCESS WITHDRAWAL
 * ==========================================
 *
 * Pending → Processing
 *
 * ADMIN ONLY
 */

const processWithdrawal = async (
  req,
  res
) => {
  try {

    const {
      withdrawalId,
    } = req.params;

    /**
     * The authenticated admin is the
     * person processing the withdrawal.
     */

    const processedBy =
      req.user._id;

    if (
      !mongoose.Types.ObjectId.isValid(
        withdrawalId
      )
    ) {
      return res.status(400).json({
        success: false,

        message:
          "Invalid withdrawal ID.",
      });
    }

    const withdrawal =
      await withdrawalService.processWithdrawal(
        withdrawalId,
        processedBy
      );

    res.json({
      success: true,

      message:
        "Withdrawal is now processing.",

      data:
        withdrawal,
    });

  } catch (error) {

    console.error(
      "PROCESS WITHDRAWAL ERROR:",
      error
    );

    res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to process withdrawal.",
    });
  }
};

/**
 * ==========================================
 * COMPLETE WITHDRAWAL
 * ==========================================
 *
 * Processing → Completed
 *
 * ADMIN ONLY
 */

const completeWithdrawal = async (
  req,
  res
) => {
  try {

    const {
      withdrawalId,
    } = req.params;

    /**
     * Authenticated admin.
     */

    const processedBy =
      req.user._id;

    if (
      !mongoose.Types.ObjectId.isValid(
        withdrawalId
      )
    ) {
      return res.status(400).json({
        success: false,

        message:
          "Invalid withdrawal ID.",
      });
    }

    const withdrawal =
      await withdrawalService.completeWithdrawal(
        withdrawalId,
        processedBy
      );

    res.json({
      success: true,

      message:
        "Withdrawal completed successfully.",

      data:
        withdrawal,
    });

  } catch (error) {

    console.error(
      "COMPLETE WITHDRAWAL ERROR:",
      error
    );

    res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to complete withdrawal.",
    });
  }
};

/**
 * ==========================================
 * REJECT WITHDRAWAL
 * ==========================================
 *
 * Pending / Processing → Rejected
 *
 * ADMIN ONLY
 */

const rejectWithdrawal = async (
  req,
  res
) => {
  try {

    const {
      withdrawalId,
    } = req.params;

    const {
      rejectionReason,
    } = req.body;

    /**
     * Authenticated admin.
     */

    const processedBy =
      req.user._id;

    if (
      !mongoose.Types.ObjectId.isValid(
        withdrawalId
      )
    ) {
      return res.status(400).json({
        success: false,

        message:
          "Invalid withdrawal ID.",
      });
    }

    const withdrawal =
      await withdrawalService.rejectWithdrawal(
        withdrawalId,

        rejectionReason,

        processedBy
      );

    res.json({
      success: true,

      message:
        "Withdrawal rejected and funds returned to wallet.",

      data:
        withdrawal,
    });

  } catch (error) {

    console.error(
      "REJECT WITHDRAWAL ERROR:",
      error
    );

    res.status(400).json({
      success: false,

      message:
        error.message ||
        "Unable to reject withdrawal.",
    });
  }
};

/**
 * ==========================================
 * GET ALL WITHDRAWALS — ADMIN
 * ==========================================
 *
 * GET
 * /api/withdrawals/admin/all
 *
 * ADMIN ONLY
 */

const getAllWithdrawals = async (
  req,
  res
) => {
  try {

    const withdrawals =
      await withdrawalService.getAllWithdrawals();

    res.json({
      success: true,

      count:
        withdrawals.length,

      data:
        withdrawals,
    });

  } catch (error) {

    console.error(
      "GET ALL WITHDRAWALS ERROR:",
      error
    );

    res.status(500).json({
      success: false,

      message:
        error.message ||
        "Unable to load withdrawals.",
    });
  }
};

/**
 * ==========================================
 * EXPORT
 * ==========================================
 */

export default {
  createWithdrawal,

  getUserWithdrawals,

  getWithdrawal,

  processWithdrawal,

  completeWithdrawal,

  rejectWithdrawal,

  getAllWithdrawals,
};