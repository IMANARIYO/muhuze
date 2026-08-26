import express from "express";

import sellerOrderController from "../controllers/sellerOrderController.js";

const router = express.Router();

/**
 * Get all orders belonging to a seller
 */
router.get(
  "/:sellerId",
  sellerOrderController.getSellerOrders
);

/**
 * Get one seller order
 */
router.get(
  "/:sellerId/:orderId",
  sellerOrderController.getSellerOrder
);

/**
 * Update seller order status
 */
router.put(
  "/:sellerId/:orderId/status",
  sellerOrderController.updateOrderStatus
);

export default router;