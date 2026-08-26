import sellerOrderService from "../services/sellerOrderService.js";

/**
 * Get all orders containing products
 * belonging to a seller.
 */
const getSellerOrders = async (req, res) => {
  try {
    const { sellerId } = req.params;

    const orders =
      await sellerOrderService.getSellerOrders(
        sellerId
      );

    res.json({
      success: true,
      count: orders.length,
      data: orders,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get one seller order.
 */
const getSellerOrder = async (req, res) => {
  try {
    const {
      sellerId,
      orderId,
    } = req.params;

    const order =
      await sellerOrderService.getSellerOrder(
        sellerId,
        orderId
      );

    if (!order) {
      return res.status(404).json({
        success: false,
        message: "Order not found.",
      });
    }

    res.json({
      success: true,
      data: order,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Update seller order status.
 */
const updateOrderStatus = async (req, res) => {
  try {
    const {
      sellerId,
      orderId,
    } = req.params;

    const { status } = req.body;

    if (!status) {
      return res.status(400).json({
        success: false,
        message: "Status is required.",
      });
    }

    const order =
      await sellerOrderService.updateOrderStatus(
        sellerId,
        orderId,
        status
      );

    if (!order) {
      return res.status(404).json({
        success: false,
        message: "Order not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Order status updated successfully.",
      data: order,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getSellerOrders,
  getSellerOrder,
  updateOrderStatus,
};