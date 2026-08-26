import express from "express";

import orderController from "../controllers/orderController.js";

const router = express.Router();


/**
 * Complete Order
 */
router.patch(
  "/:id/complete",
  orderController.completeOrder
);

/**
 * Create Order
 */
router.post(
  "/",
  orderController.createOrder
);

/**
 * Get All Orders
 */
router.get(
  "/",
  orderController.getAllOrders
);

/**
 * Buyer Orders
 */
router.get(
  "/buyer/:buyerId",
  orderController.getBuyerOrders
);

/**
 * Get Order By ID
 */
router.get(
  "/:id",
  orderController.getOrderById
);

/**
 * Update Order
 */
router.put(
  "/:id",
  orderController.updateOrder
);

/**
 * Delete Order
 */
router.delete(
  "/:id",
  orderController.deleteOrder
);

export default router;