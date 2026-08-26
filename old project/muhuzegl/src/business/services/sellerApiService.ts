import type {
  MarketplaceItem,
  UpdateMarketplaceItem,
} from "../../types/marketplaceItem";

import type {
  Order,
  OrderStatus,
} from "../../types/order";

const API_URL =
  "http://localhost:5000/api/seller";

export class SellerApiService {
  // ==========================================
  // SELLER PRODUCTS
  // ==========================================

  /**
   * Get all products belonging to a seller.
   */
  async getSellerProducts(
    sellerId: string
  ): Promise<MarketplaceItem[]> {
    const response = await fetch(
      `${API_URL}/${sellerId}/products`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch seller products."
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * Get one seller product.
   */
  async getSellerProduct(
    sellerId: string,
    productId: string
  ): Promise<MarketplaceItem> {
    const response = await fetch(
      `${API_URL}/${sellerId}/products/${productId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch seller product."
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * Update seller product.
   */
  async updateSellerProduct(
    sellerId: string,
    productId: string,
    updates: Partial<UpdateMarketplaceItem>
  ): Promise<MarketplaceItem> {
    const response = await fetch(
      `${API_URL}/${sellerId}/products/${productId}`,
      {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify(updates),
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to update seller product."
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * Delete seller product.
   */
  async deleteSellerProduct(
    sellerId: string,
    productId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_URL}/${sellerId}/products/${productId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to delete seller product."
      );
    }
  }

  // ==========================================
  // SELLER ORDERS
  // ==========================================

  /**
   * Get all orders belonging to a seller.
   */
  async getSellerOrders(
    sellerId: string
  ): Promise<Order[]> {
    const response = await fetch(
      `${API_URL}/orders/${sellerId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch seller orders."
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * Get one seller order.
   */
  async getSellerOrder(
    sellerId: string,
    orderId: string
  ): Promise<Order> {
    const response = await fetch(
      `${API_URL}/orders/${sellerId}/${orderId}`
    );

    if (!response.ok) {
      throw new Error(
        "Failed to fetch seller order."
      );
    }

    const result = await response.json();

    return result.data;
  }

  /**
   * Update seller order status.
   */
  async updateOrderStatus(
    sellerId: string,
    orderId: string,
    status: OrderStatus
  ): Promise<Order> {
    const response = await fetch(
      `${API_URL}/orders/${sellerId}/${orderId}/status`,
      {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",
        },

        body: JSON.stringify({
          status,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(
        "Failed to update order status."
      );
    }

    const result = await response.json();

    return result.data;
  }
}

export const sellerApiService =
  new SellerApiService();