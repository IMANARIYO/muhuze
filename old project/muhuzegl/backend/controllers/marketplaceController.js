import marketplaceService from "../services/marketplaceService.js";

/**
 * Create Listing
 */
const createListing = async (req, res) => {
  try {
    console.log("========== NEW MARKETPLACE REQUEST ==========");
    console.log(req.body);
    console.log("FILES:");
console.log(req.files);

const imageUrls =
  req.files?.map(
    (file) => `/uploads/${file.filename}`
  ) || [];


const listing =
  await marketplaceService.createListing({
    ...req.body,
    details: JSON.parse(req.body.details),
    images: imageUrls,
  });

    res.status(201).json({
      success: true,
      message: "Listing created successfully.",
      data: listing,
    });
  } catch (error) {
    console.error("CREATE LISTING ERROR:");
    console.error(error);

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get All Listings
 */
const getAllListings = async (req, res) => {
  try {
    const listings = await marketplaceService.getAllListings();

    res.json({
      success: true,
      count: listings.length,
      data: listings,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get Listing By ID
 */
const getListingById = async (req, res) => {
  try {
    const listing = await marketplaceService.getListingById(req.params.id);

    if (!listing) {
      return res.status(404).json({
        success: false,
        message: "Listing not found.",
      });
    }

    res.json({
      success: true,
      data: listing,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Update Listing
 */
const updateListing = async (req, res) => {
  try {
    console.log("========== UPDATE REQUEST ==========");
    console.log("ID:", req.params.id);
    console.log("BODY:", req.body);
    console.log("FILES:", req.files);

    // Existing images sent from the frontend
    let existingImages = [];

    if (req.body.existingImages) {
      existingImages = JSON.parse(req.body.existingImages);
    }

    // Newly uploaded images
    const newImages =
      req.files?.map(
        (file) => `/uploads/${file.filename}`
      ) || [];
      console.log("Existing Images:", existingImages);
console.log("New Images:", newImages);

console.log("Final Images:", [
  ...existingImages,
  ...newImages,
]);

    const updatedListing =
      await marketplaceService.updateListing(
        req.params.id,
        {
          ...req.body,
          details: JSON.parse(req.body.details),
          images: [
            ...existingImages,
            ...newImages,
          ],
        }
      );

    if (!updatedListing) {
      return res.status(404).json({
        success: false,
        message: "Listing not found.",
      });
    }

    res.json({
      success: true,
      message: "Listing updated successfully.",
      data: updatedListing,
    });

  } catch (error) {
    console.error(error);

    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};
/**
 * Delete Listing
 */
const deleteListing = async (req, res) => {
  try {
    const listing = await marketplaceService.deleteListing(req.params.id);

    if (!listing) {
      return res.status(404).json({
        success: false,
        message: "Listing not found.",
      });
    }

    res.json({
      success: true,
      message: "Listing deleted successfully.",
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Seller Listings
 */
const getSellerListings = async (req, res) => {
  try {
    const listings = await marketplaceService.getSellerListings(
      req.params.sellerId
    );

    res.json({
      success: true,
      count: listings.length,
      data: listings,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  createListing,
  getAllListings,
  getListingById,
  updateListing,
  deleteListing,
  getSellerListings,
};