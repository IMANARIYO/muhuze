import type { CartItem } from "../../types/cart";

const API_URL =
  "http://localhost:5000/api/cart";

export class CartApiService {
  /**
   * Get user's cart
   */
  async getCart(
    userId: string
  ): Promise<CartItem[]> {
    const response = await fetch(
      `${API_URL}/${userId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch cart."
      );
    }

    const result = await response.json();

    return result.data.items.map(
      (cartItem: any) => ({
        item: cartItem.itemId,
        quantity: cartItem.quantity,
      })
    );
  }

  /**
   * Add item to cart
   */
  async addToCart(
    userId: string,
    itemId: string,
    quantity: number = 1
  ): Promise<void> {
    const response = await fetch(
      API_URL,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          userId,
          itemId,
          quantity,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to add item to cart."
      );
    }
  }

  /**
   * Update item quantity
   */
  async updateQuantity(
    userId: string,
    itemId: string,
    quantity: number
  ): Promise<void> {
    const response = await fetch(
      `${API_URL}/${userId}/${itemId}`,
      {
        method: "PUT",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          quantity,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to update cart quantity."
      );
    }
  }

  /**
   * Remove item from cart
   */
  async removeFromCart(
    userId: string,
    itemId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_URL}/${userId}/${itemId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to remove item from cart."
      );
    }
  }

  /**
   * Clear cart
   */
  async clearCart(
    userId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_URL}/${userId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to clear cart."
      );
    }
  }
}

export const cartApiService =
  new CartApiService();