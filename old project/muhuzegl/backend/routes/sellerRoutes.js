import express from "express";

import sellerController from "../controllers/sellerController.js";
import sellerDashboardController from "../controllers/sellerDashboardController.js";

const router = express.Router();

/*
 * Get seller dashboard statistics
 *
 * GET /api/seller/:sellerId/dashboard
 */
router.get(
  "/:sellerId/dashboard",
  sellerDashboardController.getSellerDashboard
);

// Get all seller products
router.get(
  "/:sellerId/products",
  sellerController.getSellerProducts
);

// Get one seller product
router.get(
  "/:sellerId/products/:productId",
  sellerController.getSellerProduct
);

// Update seller product
router.put(
  "/:sellerId/products/:productId",
  sellerController.updateSellerProduct
);

// Delete seller product
router.delete(
  "/:sellerId/products/:productId",
  sellerController.deleteSellerProduct
);

export default router;