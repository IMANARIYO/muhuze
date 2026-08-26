import cartService from "../services/cartService.js";

/**
 * Get user's cart
 */
const getCart = async (req, res) => {
  try {
    const { userId } = req.params;

    const cart = await cartService.getCart(
      userId
    );

    res.json({
      success: true,
      data: cart,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Add item to cart
 */
const addToCart = async (req, res) => {
  try {
    const {
      userId,
      itemId,
      quantity,
    } = req.body;

    if (!userId || !itemId) {
      return res.status(400).json({
        success: false,
        message:
          "userId and itemId are required.",
      });
    }

    const cart =
      await cartService.addToCart(
        userId,
        itemId,
        quantity || 1
      );

    res.status(201).json({
      success: true,
      message: "Item added to cart.",
      data: cart,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Update item quantity
 */
const updateQuantity = async (
  req,
  res
) => {
  try {
    const {
      userId,
      itemId,
    } = req.params;

    const { quantity } = req.body;

    if (
      quantity === undefined ||
      quantity === null
    ) {
      return res.status(400).json({
        success: false,
        message: "Quantity is required.",
      });
    }

    const cart =
      await cartService.updateQuantity(
        userId,
        itemId,
        quantity
      );

    if (!cart) {
      return res.status(404).json({
        success: false,
        message:
          "Cart or item not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Cart quantity updated.",
      data: cart,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Remove item from cart
 */
const removeFromCart = async (
  req,
  res
) => {
  try {
    const {
      userId,
      itemId,
    } = req.params;

    const cart =
      await cartService.removeFromCart(
        userId,
        itemId
      );

    if (!cart) {
      return res.status(404).json({
        success: false,
        message:
          "Cart not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Item removed from cart.",
      data: cart,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

/**
 * Clear cart
 */
const clearCart = async (
  req,
  res
) => {
  try {
    const { userId } = req.params;

    const cart =
      await cartService.clearCart(
        userId
      );

    if (!cart) {
      return res.status(404).json({
        success: false,
        message:
          "Cart not found.",
      });
    }

    res.json({
      success: true,
      message:
        "Cart cleared successfully.",
      data: cart,
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

export default {
  getCart,
  addToCart,
  updateQuantity,
  removeFromCart,
  clearCart,
};