import express from "express";

import cartController from "../controllers/cartController.js";

const router = express.Router();

/**
 * Get user's cart
 */
router.get(
  "/:userId",
  cartController.getCart
);

/**
 * Add item to cart
 */
router.post(
  "/",
  cartController.addToCart
);

/**
 * Update item quantity
 */
router.put(
  "/:userId/:itemId",
  cartController.updateQuantity
);

/**
 * Remove item from cart
 */
router.delete(
  "/:userId/:itemId",
  cartController.removeFromCart
);

/**
 * Clear user's cart
 */
router.delete(
  "/:userId",
  cartController.clearCart
);

export default router;