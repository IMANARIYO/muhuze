import express from "express";

import wishlistController from "../controllers/wishlistController.js";

const router = express.Router();

/**
 * Add item to wishlist
 */
router.post(
  "/",
  wishlistController.addToWishlist
);

/**
 * Get user's wishlist
 */
router.get(
  "/:userId",
  wishlistController.getWishlist
);

/**
 * Check if item is in wishlist
 */
router.get(
  "/:userId/:itemId",
  wishlistController.isInWishlist
);

/**
 * Remove item from wishlist
 */
router.delete(
  "/:userId/:itemId",
  wishlistController.removeFromWishlist
);

/**
 * Clear user's wishlist
 */
router.delete(
  "/:userId",
  wishlistController.clearWishlist
);

export default router;