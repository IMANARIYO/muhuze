import Wishlist from "../models/Wishlist.js";

class WishlistService {
  /**
   * Add item to wishlist
   */
  async addToWishlist(userId, itemId) {
    return await Wishlist.findOneAndUpdate(
      {
        userId,
        itemId,
      },
      {
        userId,
        itemId,
      },
      {
        new: true,
        upsert: true,
      }
    );
  }

  /**
   * Get user's wishlist
   */
  async getWishlist(userId) {
    return await Wishlist.find({
      userId,
    })
      .populate("itemId")
      .sort({
        createdAt: -1,
      });
  }

  /**
   * Check if item is in wishlist
   */
  async isInWishlist(userId, itemId) {
    return await Wishlist.findOne({
      userId,
      itemId,
    });
  }

  /**
   * Remove item from wishlist
   */
  async removeFromWishlist(userId, itemId) {
    return await Wishlist.findOneAndDelete({
      userId,
      itemId,
    });
  }

  /**
   * Clear user's wishlist
   */
  async clearWishlist(userId) {
    return await Wishlist.deleteMany({
      userId,
    });
  }
}

export default new WishlistService();