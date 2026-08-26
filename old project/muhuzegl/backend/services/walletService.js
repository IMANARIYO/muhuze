import mongoose from "mongoose";

import Wallet from "../models/Wallet.js";
import WalletTransaction from "../models/WalletTransaction.js";
import ReferralCommission from "../models/ReferralCommission.js";

/**
 * ============================================================
 * SUPPORTED WALLET CURRENCIES
 * ============================================================
 */

const SUPPORTED_CURRENCIES = [
  "RWF",
  "USD",
  "USDT",
  "USDC",

];

/**
 * ============================================================
 * NORMALIZE CURRENCY
 * ============================================================
 */

const normalizeCurrency = (currency) => {
  if (!currency) {
    throw new Error("Currency is required.");
  }

  const normalized = String(currency)
    .trim()
    .toUpperCase();

  if (!SUPPORTED_CURRENCIES.includes(normalized)) {
    throw new Error(
      `Unsupported wallet currency: ${normalized}`
    );
  }

  return normalized;
};
/**
 * ============================================================
 * GET CURRENCY WALLET
 * ============================================================
 *
 * MUHUZE WALLET ACCOUNTING:
 *
 * RWF  -> wallet.rwf
 *
 * USD  -> wallet.usd
 * USDT -> wallet.usd
 * USDC -> wallet.usd
 *
 * USD, USDT and USDC are all treated
 * as USD-based wallet value.
 */

const getCurrencyWallet = (
  wallet,
  currency
) => {
  const normalized =
    normalizeCurrency(currency);

  // RWF remains a separate wallet
  if (normalized === "RWF") {
    return wallet.rwf;
  }

  // USD-based wallet
  if (
    normalized === "USD" ||
    normalized === "USDT" ||
    normalized === "USDC"
  ) {
    return wallet.usd;
  }

  throw new Error(
    `Unsupported wallet currency: ${normalized}`
  );
};

/**
 * ============================================================
 * GET OR CREATE WALLET
 * ============================================================
 */

const getOrCreateWallet = async (
  userId,
  session = null
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

  const query = Wallet.findOne({
    userId,
  });

  if (session) {
    query.session(session);
  }

  let wallet = await query;

  /**
   * ==========================================================
   * CREATE NEW MULTI-CURRENCY WALLET
   * ==========================================================
   */

  if (!wallet) {
    const walletData = {
      userId,

      rwf: {
        balance: 0,
        pendingBalance: 0,
        totalEarned: 0,
        totalWithdrawn: 0,
      },

      usd: {
        balance: 0,
        pendingBalance: 0,
        totalEarned: 0,
        totalWithdrawn: 0,
      },

      crypto: {
        usdt: {
          balance: 0,
          pendingBalance: 0,
          totalEarned: 0,
          totalWithdrawn: 0,
        },

        usdc: {
          balance: 0,
          pendingBalance: 0,
          totalEarned: 0,
          totalWithdrawn: 0,
        },

        btc: {
          balance: 0,
          pendingBalance: 0,
          totalEarned: 0,
          totalWithdrawn: 0,
        },
      },

      status: "Active",
    };

    if (session) {
      const created =
        await Wallet.create(
          [walletData],
          {
            session,
          }
        );

      wallet = created[0];
    } else {
      wallet =
        await Wallet.create(
          walletData
        );
    }
  }

  /**
   * ==========================================================
   * PROTECT AGAINST OLD WALLET DOCUMENTS
   * ==========================================================
   *
   * Existing wallets may have been created using the old
   * single-currency structure.
   *
   * Make sure the new structure exists before using it.
   */

  let changed = false;

  if (!wallet.rwf) {
    wallet.rwf = {
      balance: 0,
      pendingBalance: 0,
      totalEarned: 0,
      totalWithdrawn: 0,
    };

    changed = true;
  }

  if (!wallet.usd) {
    wallet.usd = {
      balance: 0,
      pendingBalance: 0,
      totalEarned: 0,
      totalWithdrawn: 0,
    };

    changed = true;
  }

  if (!wallet.crypto) {
    wallet.crypto = {};

    changed = true;
  }

  if (!wallet.crypto.usdt) {
    wallet.crypto.usdt = {
      balance: 0,
      pendingBalance: 0,
      totalEarned: 0,
      totalWithdrawn: 0,
    };

    changed = true;
  }

  if (!wallet.crypto.usdc) {
    wallet.crypto.usdc = {
      balance: 0,
      pendingBalance: 0,
      totalEarned: 0,
      totalWithdrawn: 0,
    };

    changed = true;
  }

  if (!wallet.crypto.btc) {
    wallet.crypto.btc = {
      balance: 0,
      pendingBalance: 0,
      totalEarned: 0,
      totalWithdrawn: 0,
    };

    changed = true;
  }

  if (changed) {
    await wallet.save(
      session
        ? { session }
        : undefined
    );
  }

  return wallet;
};

/**
 * ============================================================
 * GET WALLET
 * ============================================================
 */

const getWallet = async (
  userId
) => {
  return await getOrCreateWallet(
    userId
  );
};

/**
 * ============================================================
 * ADD PENDING COMMISSION
 * ============================================================
 *
 * Referral commissions are NOT immediately withdrawable.
 *
 * Currency is taken from ReferralCommission.
 *
 * referenceId = ReferralCommission._id
 */

const addPendingCommission = async (
  userId,
  amount,
  commissionId,
  session = null
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
      commissionId
    )
  ) {
    throw new Error(
      "Invalid commission ID."
    );
  }

  const numericAmount =
    Number(amount);

  if (
    !Number.isFinite(
      numericAmount
    ) ||
    numericAmount <= 0
  ) {
    throw new Error(
      "Commission amount must be greater than zero."
    );
  }

  /**
   * ==========================================================
   * FIND COMMISSION
   * ==========================================================
   */

  const commissionQuery =
    ReferralCommission.findById(
      commissionId
    );

  if (session) {
    commissionQuery.session(
      session
    );
  }

  const commission =
    await commissionQuery;

  if (!commission) {
    throw new Error(
      "Referral commission not found."
    );
  }

  const currency =
    normalizeCurrency(
      commission.currency
    );

  /**
   * ==========================================================
   * DUPLICATE PROTECTION
   * ==========================================================
   *
   * Do not add the same commission twice.
   */

  const existingQuery =
    WalletTransaction.findOne({
      userId,
      referenceId:
        commissionId,
      type:
        "REFERRAL_COMMISSION",
    });

  if (session) {
    existingQuery.session(
      session
    );
  }

  const existing =
    await existingQuery;

  if (existing) {
    return existing;
  }

  /**
   * ==========================================================
   * GET WALLET
   * ==========================================================
   */

  const wallet =
    await getOrCreateWallet(
      userId,
      session
    );

  if (
    wallet.status !== "Active"
  ) {
    throw new Error(
      "Wallet is not active."
    );
  }

  const currencyWallet =
    getCurrencyWallet(
      wallet,
      currency
    );

  /**
   * ==========================================================
   * ADD TO PENDING BALANCE
   * ==========================================================
   */

  currencyWallet.pendingBalance +=
    numericAmount;

  /**
   * ==========================================================
   * CREATE TRANSACTION
   * ==========================================================
   */

  const transactionData = {
    userId,

    type:
      "REFERRAL_COMMISSION",

    amount:
      numericAmount,

    currency,

    referenceId:
      commissionId,

    referenceType:
      "ReferralCommission",

    status:
      "Pending",

    description:
      commission.description ||
      "Referral commission pending release.",
  };

  let transaction;

  if (session) {
    const created =
      await WalletTransaction.create(
        [transactionData],
        {
          session,
        }
      );

    transaction =
      created[0];
  } else {
    transaction =
      await WalletTransaction.create(
        transactionData
      );
  }

  /**
   * ==========================================================
   * SAVE WALLET
   * ==========================================================
   */

  await wallet.save(
    session
      ? { session }
      : undefined
  );

  return transaction;
};

/**
 * ============================================================
 * MAKE COMMISSION AVAILABLE
 * ============================================================
 *
 * Moves money:
 *
 * pendingBalance
 *       ↓
 * balance
 *
 * and updates the transaction status.
 */

const makeCommissionAvailable =
  async (
    userId,
    amount,
    commissionId,
    session = null
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
        commissionId
      )
    ) {
      throw new Error(
        "Invalid commission ID."
      );
    }

    const numericAmount =
      Number(amount);

    if (
      !Number.isFinite(
        numericAmount
      ) ||
      numericAmount <= 0
    ) {
      throw new Error(
        "Commission amount must be greater than zero."
      );
    }

    /**
     * ========================================================
     * FIND COMMISSION
     * ========================================================
     */

    const commissionQuery =
      ReferralCommission.findById(
        commissionId
      );

    if (session) {
      commissionQuery.session(
        session
      );
    }

    const commission =
      await commissionQuery;

    if (!commission) {
      throw new Error(
        "Referral commission not found."
      );
    }

    const currency =
      normalizeCurrency(
        commission.currency
      );

    /**
     * ========================================================
     * GET WALLET
     * ========================================================
     */

    const wallet =
      await getOrCreateWallet(
        userId,
        session
      );

    if (
      wallet.status !== "Active"
    ) {
      throw new Error(
        "Wallet is not active."
      );
    }

    const currencyWallet =
      getCurrencyWallet(
        wallet,
        currency
      );

    /**
     * ========================================================
     * FIND PENDING TRANSACTION
     * ========================================================
     */

    const transactionQuery =
      WalletTransaction.findOne({
        userId,

        referenceId:
          commissionId,

        type:
          "REFERRAL_COMMISSION",
      });

    if (session) {
      transactionQuery.session(
        session
      );
    }

    const transaction =
      await transactionQuery;

    /**
     * ========================================================
     * ALREADY RELEASED
     * ========================================================
     */

    if (
      transaction &&
      transaction.status ===
        "Completed"
    ) {
      return transaction;
    }

    /**
     * ========================================================
     * PROTECT AGAINST NEGATIVE PENDING BALANCE
     * ========================================================
     */

    if (
      currencyWallet.pendingBalance <
      numericAmount
    ) {
      throw new Error(
        `Insufficient pending ${currency} balance.`
      );
    }

    /**
     * ========================================================
     * MOVE PENDING → AVAILABLE
     * ========================================================
     */

    currencyWallet.pendingBalance -=
      numericAmount;

    currencyWallet.balance +=
      numericAmount;

    currencyWallet.totalEarned +=
      numericAmount;

    /**
     * ========================================================
     * UPDATE TRANSACTION
     * ========================================================
     */

    if (transaction) {
      transaction.status =
        "Completed";

      transaction.amount =
        numericAmount;

      transaction.currency =
        currency;

      await transaction.save(
        session
          ? { session }
          : undefined
      );
    } else {
      const transactionData = {
        userId,

        type:
          "REFERRAL_COMMISSION",

        amount:
          numericAmount,

        currency,

        referenceId:
          commissionId,

        referenceType:
          "ReferralCommission",

        status:
          "Completed",

        description:
          commission.description ||
          "Referral commission released.",
      };

      if (session) {
        const created =
          await WalletTransaction.create(
            [transactionData],
            {
              session,
            }
          );

        returnTransaction =
          created[0];
      } else {
        returnTransaction =
          await WalletTransaction.create(
            transactionData
          );
      }
    }

    /**
     * ========================================================
     * SAVE WALLET
     * ========================================================
     */

    await wallet.save(
      session
        ? { session }
        : undefined
    );

    return (
      transaction ||
      returnTransaction
    );
  };

/**
 * ============================================================
 * CREDIT SELLER REVENUE
 * ============================================================
 *
 * Adds seller earnings directly to the available balance.
 *
 * currency comes from the order/revenue transaction.
 */

const creditSellerRevenue =
  async (
    userId,
    amount,
    revenueTransactionId,
    currency,
    session = null
  ) => {
    if (
      !mongoose.Types.ObjectId.isValid(
        userId
      )
    ) {
      throw new Error(
        "Invalid seller ID."
      );
    }

    if (
      !mongoose.Types.ObjectId.isValid(
        revenueTransactionId
      )
    ) {
      throw new Error(
        "Invalid revenue transaction ID."
      );
    }

    const numericAmount =
      Number(amount);

    if (
      !Number.isFinite(
        numericAmount
      ) ||
      numericAmount <= 0
    ) {
      throw new Error(
        "Seller revenue amount must be greater than zero."
      );
    }

    const normalizedCurrency =
      normalizeCurrency(
        currency
      );

    /**
     * ========================================================
     * DUPLICATE PROTECTION
     * ========================================================
     */

    const existingQuery =
      WalletTransaction.findOne({
        userId,

        referenceId:
          revenueTransactionId,

        type:
          "SELLER_REVENUE",
      });

    if (session) {
      existingQuery.session(
        session
      );
    }

    const existing =
      await existingQuery;

    if (existing) {
      return existing;
    }

    /**
     * ========================================================
     * GET WALLET
     * ========================================================
     */

    const wallet =
      await getOrCreateWallet(
        userId,
        session
      );

    if (
      wallet.status !== "Active"
    ) {
      throw new Error(
        "Wallet is not active."
      );
    }

    const currencyWallet =
      getCurrencyWallet(
        wallet,
        normalizedCurrency
      );

    /**
     * ========================================================
     * CREDIT BALANCE
     * ========================================================
     */

    currencyWallet.balance +=
      numericAmount;

    currencyWallet.totalEarned +=
      numericAmount;

    /**
     * ========================================================
     * CREATE TRANSACTION
     * ========================================================
     */

    const transactionData = {
      userId,

      type:
        "SELLER_REVENUE",

      amount:
        numericAmount,

      currency:
        normalizedCurrency,

      referenceId:
        revenueTransactionId,

      referenceType:
        "RevenueTransaction",

      status:
        "Completed",

      description:
        "Seller revenue credited.",
    };

    let transaction;

    if (session) {
      const created =
        await WalletTransaction.create(
          [transactionData],
          {
            session,
          }
        );

      transaction =
        created[0];
    } else {
      transaction =
        await WalletTransaction.create(
          transactionData
        );
    }

    /**
     * ========================================================
     * SAVE
     * ========================================================
     */

    await wallet.save(
      session
        ? { session }
        : undefined
    );

    return transaction;
  };

/**
 * ============================================================
 * GET WALLET TRANSACTIONS
 * ============================================================
 */

const getWalletTransactions =
  async (
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
 * ============================================================
 * EXPORT
 * ============================================================
 */

export default {
  getOrCreateWallet,
  getWallet,

  addPendingCommission,
  makeCommissionAvailable,

  creditSellerRevenue,

  getWalletTransactions,

  normalizeCurrency,
  getCurrencyWallet,
};