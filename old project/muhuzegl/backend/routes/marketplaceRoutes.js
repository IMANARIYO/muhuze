import express from "express";

import marketplaceController from "../controllers/marketplaceController.js";
import upload from "../middleware/upload.js";

const router = express.Router();

/**
 * Create Listing
 */
router.post(
  "/",
  upload.array("images", 10),
  marketplaceController.createListing
);

/**
 * Get All Listings
 */
router.get(
  "/",
  marketplaceController.getAllListings
);

/**
 * Seller Listings
 */
router.get(
  "/seller/:sellerId",
  marketplaceController.getSellerListings
);

/**
 * Get Listing By ID
 */
router.get(
  "/:id",
  marketplaceController.getListingById
);

/**
 * Update Listing
 */
router.put(
  "/:id",
  upload.array("images", 10),
  marketplaceController.updateListing
);

/**
 * Delete Listing
 */
router.delete(
  "/:id",
  marketplaceController.deleteListing
);

export default router;