import orderService from "../services/orderService.js";

/**
 * Create Order
 */
const createOrder = async (req, res) => {
  try {
    const order = await orderService.createOrder(req.body);

    res.status(201).json({
      success: true,
      message: "Order placed successfully.",
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
 * Get All Orders
 */
const getAllOrders = async (req, res) => {
  try {
    const orders = await orderService.getAllOrders();

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
 * Get Order By ID
 */
const getOrderById = async (req, res) => {
  try {
    const order = await orderService.getOrderById(
      req.params.id
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
 * Buyer Orders
 */
const getBuyerOrders = async (req, res) => {
  try {
    const orders =
      await orderService.getBuyerOrders(
        req.params.buyerId
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
 * Update Order
 */
const updateOrder = async (req, res) => {
  try {
    const order =
      await orderService.updateOrder(
        req.params.id,
        req.body
      );

    if (!order) {
      return res.status(404).json({
        success: false,
        message: "Order not found.",
      });
    }

    res.json({
      success: true,
      message: "Order updated successfully.",
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
 * ==========================================
 * COMPLETE ORDER
 * ==========================================
 */

const completeOrder = async (req, res) => {
  try {
    const order =
      await orderService.completeOrder(
        req.params.id
      );

    res.status(200).json({
      success: true,
      message:
        "Order completed and seller revenue credited successfully.",
      data: order,
    });

  } catch (error) {
    console.error(
      "COMPLETE ORDER ERROR:",
      error
    );

    res.status(400).json({
      success: false,
      message:
        error.message ||
        "Unable to complete order.",
    });
  }
};
/**
 * Delete Order
 */
const deleteOrder = async (req, res) => {
  try {
    const order =
      await orderService.deleteOrder(
        req.params.id
      );

    if (!order) {
      return res.status(404).json({
        success: false,
        message: "Order not found.",
      });
    }

    res.json({
      success: true,
      message: "Order deleted successfully.",
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  createOrder,
  getAllOrders,
  getOrderById,
  getBuyerOrders,
  updateOrder,
  completeOrder,
  deleteOrder,
};