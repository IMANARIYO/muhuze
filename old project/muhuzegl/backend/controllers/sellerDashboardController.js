import sellerDashboardService from "../services/sellerDashboardService.js";

/**
 * Get seller dashboard statistics.
 */
const getSellerDashboard = async (req, res) => {
  try {
    const { sellerId } = req.params;

    if (!sellerId) {
      return res.status(400).json({
        success: false,
        message: "Seller ID is required.",
      });
    }

    const stats =
      await sellerDashboardService.getDashboardStats(
        sellerId
      );

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    console.error(
      "Get seller dashboard error:",
      error
    );

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getSellerDashboard,
};