import sellerService from "../services/sellerService.js";

/**
 * Get all products belonging to a seller
 */
const getSellerProducts = async (
  req,
  res
) => {
  try {
    const { sellerId } = req.params;

    const products =
      await sellerService.getSellerProducts(
        sellerId
      );

    res.json({
      success: true,
      count: products.length,
      data: products,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Get one seller product
 */
const getSellerProduct = async (
  req,
  res
) => {
  try {
    const {
      sellerId,
      productId,
    } = req.params;

    const product =
      await sellerService.getSellerProduct(
        sellerId,
        productId
      );

    if (!product) {
      return res.status(404).json({
        success: false,
        message:
          "Product not found.",
      });
    }

    res.json({
      success: true,
      data: product,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Update seller product
 */
const updateSellerProduct = async (
  req,
  res
) => {
  try {
    const {
      sellerId,
      productId,
    } = req.params;

    const product =
      await sellerService.updateSellerProduct(
        sellerId,
        productId,
        req.body
      );

    if (!product) {
      return res.status(404).json({
        success: false,
        message:
          "Product not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Product updated successfully.",
      data: product,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Delete seller product
 */
const deleteSellerProduct = async (
  req,
  res
) => {
  try {
    const {
      sellerId,
      productId,
    } = req.params;

    const product =
      await sellerService.deleteSellerProduct(
        sellerId,
        productId
      );

    if (!product) {
      return res.status(404).json({
        success: false,
        message:
          "Product not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Product deleted successfully.",
      data: product,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getSellerProducts,
  getSellerProduct,
  updateSellerProduct,
  deleteSellerProduct,
};