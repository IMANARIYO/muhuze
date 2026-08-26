import wishlistService from "../services/wishlistService.js";

/**
 * Add item to wishlist
 */
const addToWishlist = async (req, res) => {
  try {
    const { userId, itemId } = req.body;

    if (!userId || !itemId) {
      return res.status(400).json({
        success: false,
        message: "userId and itemId are required.",
      });
    }

    const wishlistItem =
      await wishlistService.addToWishlist(
        userId,
        itemId
      );

    res.status(201).json({
      success: true,
      message: "Item added to wishlist.",
      data: wishlistItem,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get user's wishlist
 */
const getWishlist = async (req, res) => {
  try {
    const { userId } = req.params;

    const wishlist =
      await wishlistService.getWishlist(userId);

    res.json({
      success: true,
      count: wishlist.length,
      data: wishlist,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Check wishlist
 */
const isInWishlist = async (req, res) => {
  try {
    const { userId, itemId } = req.params;

    const wishlistItem =
      await wishlistService.isInWishlist(
        userId,
        itemId
      );

    res.json({
      success: true,
      isInWishlist: !!wishlistItem,
      data: wishlistItem,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Remove item from wishlist
 */
const removeFromWishlist = async (req, res) => {
  try {
    const { userId, itemId } = req.params;

    const wishlistItem =
      await wishlistService.removeFromWishlist(
        userId,
        itemId
      );

    if (!wishlistItem) {
      return res.status(404).json({
        success: false,
        message: "Wishlist item not found.",
      });
    }

    res.json({
      success: true,
      message: "Item removed from wishlist.",
      data: wishlistItem,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Clear wishlist
 */
const clearWishlist = async (req, res) => {
  try {
    const { userId } = req.params;

    const result =
      await wishlistService.clearWishlist(userId);

    res.json({
      success: true,
      message: "Wishlist cleared successfully.",
      deletedCount: result.deletedCount,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  addToWishlist,
  getWishlist,
  isInWishlist,
  removeFromWishlist,
  clearWishlist,
};