import Marketplace from "../models/Marketplace.js";

class SellerService {
  /**
   * Get all products belonging to a seller
   */
  async getSellerProducts(sellerId) {
    return await Marketplace.find({
      sellerId,
    }).sort({
      createdAt: -1,
    });
  }

  /**
   * Get one seller product
   */
  async getSellerProduct(
    sellerId,
    productId
  ) {
    return await Marketplace.findOne({
      _id: productId,
      sellerId,
    });
  }

  /**
   * Update seller product
   */
  async updateSellerProduct(
    sellerId,
    productId,
    updates
  ) {
    return await Marketplace.findOneAndUpdate(
      {
        _id: productId,
        sellerId,
      },
      updates,
      {
        new: true,
        runValidators: true,
      }
    );
  }

  /**
   * Delete seller product
   */
  async deleteSellerProduct(
    sellerId,
    productId
  ) {
    return await Marketplace.findOneAndDelete({
      _id: productId,
      sellerId,
    });
  }
}

export default new SellerService();