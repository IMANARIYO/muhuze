import walletService from "../services/walletService.js";

/**
 * ==========================================
 * GET CURRENT USER WALLET
 * ==========================================
 */

const getWallet = async (req, res) => {
  try {
    const wallet =
      await walletService.getWallet(
        req.user._id
      );

    res.status(200).json({
      success: true,
      data: wallet,
    });

  } catch (error) {
    console.error(
      "GET WALLET ERROR:",
      error
    );

    res.status(500).json({
      success: false,
      message:
        error.message ||
        "Unable to load wallet.",
    });
  }
};

/**
 * ==========================================
 * GET CURRENT USER WALLET TRANSACTIONS
 * ==========================================
 */

const getWalletTransactions =
  async (req, res) => {
    try {
      const transactions =
        await walletService.getWalletTransactions(
          req.user._id
        );

      res.status(200).json({
        success: true,
        count: transactions.length,
        data: transactions,
      });

    } catch (error) {
      console.error(
        "GET WALLET TRANSACTIONS ERROR:",
        error
      );

      res.status(500).json({
        success: false,
        message:
          error.message ||
          "Unable to load wallet transactions.",
      });
    }
  };

export default {
  getWallet,
  getWalletTransactions,
};