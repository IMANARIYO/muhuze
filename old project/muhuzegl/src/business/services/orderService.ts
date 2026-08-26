import type {
  CreateOrder,
  Order,
  OrderStatus,
} from "../../types/order";

import { apiClient } from "./apiClient";

interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export class OrderService {

  /**
   * ==========================================
   * GET ALL ORDERS
   * ==========================================
   */
  async getAll(): Promise<Order[]> {
    const result =
      await apiClient.get<ApiResponse<Order[]>>(
        "/orders"
      );

    return result.data;
  }

  /**
   * ==========================================
   * GET ORDER BY ID
   * ==========================================
   */
  async findById(
    id: string
  ): Promise<Order> {
    const result =
      await apiClient.get<ApiResponse<Order>>(
        `/orders/${id}`
      );

    return result.data;
  }

  /**
   * ==========================================
   * GET ORDERS BY BUYER
   * ==========================================
   */
  async findByBuyer(
    buyerId: string
  ): Promise<Order[]> {
    const result =
      await apiClient.get<ApiResponse<Order[]>>(
        `/orders/buyer/${buyerId}`
      );

    return result.data;
  }

  /**
   * ==========================================
   * CREATE ORDER
   * ==========================================
   *
   * IMPORTANT:
   *
   * The backend expects:
   *
   * products: [
   *   {
   *     productId,
   *     quantity
   *   }
   * ]
   *
   * The backend calculates the real
   * product prices itself.
   */
  async create(
    order: CreateOrder
  ): Promise<Order> {

    const result =
      await apiClient.post<ApiResponse<Order>>(
        "/orders",
        {
          buyerId:
            order.buyerId,

          buyer:
            order.buyer,

          products:
            order.products.map(
              (product) => ({
                productId:
                  this.getProductId(
                    product
                  ),

                quantity:
                  product.quantity,
              })
            ),

          deliveryAddress:
            order.deliveryAddress,

          paymentMethod:
            order.paymentMethod,
        }
      );

    return result.data;
  }

  /**
   * ==========================================
   * UPDATE ORDER
   * ==========================================
   */
  async update(
    order: Order
  ): Promise<Order> {

    const result =
      await apiClient.put<ApiResponse<Order>>(
        `/orders/${order._id}`,
        {
          buyerId:
            order.buyerId,

          buyer:
            order.buyer,

          products:
            order.products.map(
              (product) => ({
                productId:
                  this.getProductId(
                    product
                  ),

                quantity:
                  product.quantity,
              })
            ),

          deliveryAddress:
            order.deliveryAddress,

          paymentMethod:
            order.paymentMethod,

          status:
            order.status,
        }
      );

    return result.data;
  }

  /**
   * ==========================================
   * UPDATE ORDER STATUS
   * ==========================================
   */
  async updateStatus(
    id: string,
    status: OrderStatus
  ): Promise<Order> {

    const result =
      await apiClient.put<ApiResponse<Order>>(
        `/orders/${id}`,
        {
          status,
        }
      );

    return result.data;
  }

  /**
   * ==========================================
   * DELETE ORDER
   * ==========================================
   */
  async delete(
    id: string
  ): Promise<void> {

    await apiClient.delete<ApiResponse<null>>(
      `/orders/${id}`
    );
  }

  /**
   * ==========================================
   * GET PRODUCT ID
   * ==========================================
   *
   * Supports the product structures
   * currently used by the frontend.
   */
  private getProductId(
    product: any
  ): string {

    const productId =
      product.productId ??
      product.item?._id ??
      product.item?.id;

    if (!productId) {
      throw new Error(
        "Order product is missing a product ID."
      );
    }

    return String(productId);
  }
}

export const orderService =
  new OrderService();