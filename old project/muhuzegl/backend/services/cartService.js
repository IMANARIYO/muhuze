import Cart from "../models/Cart.js";

class CartService {
  /**
   * Get user's cart
   */
  async getCart(userId) {
    let cart = await Cart.findOne({
      userId,
    }).populate("items.itemId");

    // Create an empty cart if one doesn't exist
    if (!cart) {
      cart = await Cart.create({
        userId,
        items: [],
      });
    }

    return cart;
  }

  /**
   * Add item to cart
   */
  async addToCart(
    userId,
    itemId,
    quantity = 1
  ) {
    let cart = await Cart.findOne({
      userId,
    });

    if (!cart) {
      cart = await Cart.create({
        userId,
        items: [
          {
            itemId,
            quantity,
          },
        ],
      });

      return await cart.populate(
        "items.itemId"
      );
    }

    const existingItem =
      cart.items.find(
        (item) =>
          item.itemId.toString() === itemId
      );

    if (existingItem) {
      existingItem.quantity += quantity;
    } else {
      cart.items.push({
        itemId,
        quantity,
      });
    }

    await cart.save();

    return await cart.populate(
      "items.itemId"
    );
  }

  /**
   * Update quantity
   */
  async updateQuantity(
    userId,
    itemId,
    quantity
  ) {
    const cart = await Cart.findOne({
      userId,
    });

    if (!cart) {
      return null;
    }

    const item = cart.items.find(
      (cartItem) =>
        cartItem.itemId.toString() === itemId
    );

    if (!item) {
      return null;
    }

    if (quantity <= 0) {
      cart.items = cart.items.filter(
        (cartItem) =>
          cartItem.itemId.toString() !==
          itemId
      );
    } else {
      item.quantity = quantity;
    }

    await cart.save();

    return await cart.populate(
      "items.itemId"
    );
  }

  /**
   * Remove item from cart
   */
  async removeFromCart(
    userId,
    itemId
  ) {
    const cart = await Cart.findOne({
      userId,
    });

    if (!cart) {
      return null;
    }

    cart.items = cart.items.filter(
      (item) =>
        item.itemId.toString() !== itemId
    );

    await cart.save();

    return await cart.populate(
      "items.itemId"
    );
  }

  /**
   * Clear cart
   */
  async clearCart(userId) {
    const cart = await Cart.findOne({
      userId,
    });

    if (!cart) {
      return null;
    }

    cart.items = [];

    await cart.save();

    return cart;
  }
}

export default new CartService();