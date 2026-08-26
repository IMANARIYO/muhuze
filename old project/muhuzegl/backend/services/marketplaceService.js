import Marketplace from "../models/Marketplace.js";

class MarketplaceService {
  /**
   * Create Listing
   */
  async createListing(data) {
    const listing = await Marketplace.create(data);

    return listing;
  }

  /**
   * Get All Listings
   */
  async getAllListings() {
    return await Marketplace.find()
      .populate(
        "sellerId",
        "fullName email phone profileImage"
      )
      .sort({
        createdAt: -1,
      });
  }

  /**
   * Get Listing By ID
   */
  async getListingById(id) {
    return await Marketplace.findById(id)
      .populate(
        "sellerId",
        "fullName email phone profileImage"
      );
  }
  
  /**
   * Update Listing
   */
  async updateListing(id, data) {
    return await Marketplace.findByIdAndUpdate(
      id,
      data,
      {
        new: true,
      }
    );
  }

  /**
   * Delete Listing
   */
  async deleteListing(id) {
    return await Marketplace.findByIdAndDelete(id);
  }

  /**
   * Seller Listings
   */
  async getSellerListings(sellerId) {
    return await Marketplace.find({
      sellerId,
    }).sort({
      createdAt: -1,
    });
  }
}

export default new MarketplaceService();