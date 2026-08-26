import type { MarketplaceItem } from "../../types/marketplaceItem";

const API_URL =
  "http://localhost:5000/api/wishlist";

export class WishlistApiService {
  /**
   * Get user's wishlist
   */
  async getWishlist(
    userId: string
  ): Promise<MarketplaceItem[]> {
    const response = await fetch(
      `${API_URL}/${userId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch wishlist."
      );
    }

    const result = await response.json();

    return result.data.map(
      (wishlistItem: any) =>
        wishlistItem.itemId
    );
  }

  /**
   * Add item to wishlist
   */
  async addToWishlist(
    userId: string,
    itemId: string
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
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to add item to wishlist."
      );
    }
  }

  /**
   * Check if item is in wishlist
   */
  async isInWishlist(
    userId: string,
    itemId: string
  ): Promise<boolean> {
    const response = await fetch(
      `${API_URL}/${userId}/${itemId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to check wishlist."
      );
    }

    const result = await response.json();

    return result.isInWishlist;
  }

  /**
   * Remove item from wishlist
   */
  async removeFromWishlist(
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
        "Failed to remove item from wishlist."
      );
    }
  }

  /**
   * Clear wishlist
   */
  async clearWishlist(
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
        "Failed to clear wishlist."
      );
    }
  }
}

export const wishlistApiService =
  new WishlistApiService();