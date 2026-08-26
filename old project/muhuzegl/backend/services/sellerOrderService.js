import Order from "../models/Order.js";
import revenueService from "./revenueService.js";

class SellerOrderService {
  /**
   * =====================================================
   * CHECK WHETHER ORDER BELONGS TO SELLER
   * =====================================================
   */
  hasSellerProduct(order, sellerId) {
    return order.products.some((product) => {
      /*
       * Preferred location:
       * product.sellerId
       */
      if (product.sellerId) {
        /*
         * If sellerId is populated:
         *
         * {
         *   _id: "...",
         *   fullName: "...",
         *   email: "..."
         * }
         */
        if (
          typeof product.sellerId === "object" &&
          product.sellerId._id
        ) {
          return (
            product.sellerId._id.toString() ===
            sellerId.toString()
          );
        }

        /*
         * Normal ObjectId
         */
        return (
          product.sellerId.toString() ===
          sellerId.toString()
        );
      }

      /*
       * =================================================
       * FALLBACK
       * product.item.sellerId
       * =================================================
       */

      const itemSellerId =
        product.item?.sellerId;

      if (!itemSellerId) {
        return false;
      }

      /*
       * Populated seller
       */
      if (
        typeof itemSellerId === "object" &&
        itemSellerId._id
      ) {
        return (
          itemSellerId._id.toString() ===
          sellerId.toString()
        );
      }

      /*
       * ObjectId/string
       */
      return (
        itemSellerId.toString() ===
        sellerId.toString()
      );
    });
  }

  /**
   * =====================================================
   * GET ALL ORDERS BELONGING TO SELLER
   * =====================================================
   */
  async getSellerOrders(sellerId) {
    const orders = await Order.find()
      .sort({
        createdAt: -1,
      })
      .populate(
        "products.item.sellerId",
        "fullName email phone"
      );

    return orders.filter((order) =>
      this.hasSellerProduct(
        order,
        sellerId
      )
    );
  }

  /**
   * =====================================================
   * GET ONE SELLER ORDER
   * =====================================================
   */
  async getSellerOrder(
    sellerId,
    orderId
  ) {
    const order =
      await Order.findById(orderId)
        .populate(
          "products.item.sellerId",
          "fullName email phone"
        );

    if (!order) {
      return null;
    }

    const belongsToSeller =
      this.hasSellerProduct(
        order,
        sellerId
      );

    if (!belongsToSeller) {
      return null;
    }

    return order;
  }

  /**
   * =====================================================
   * UPDATE SELLER ORDER STATUS
   * =====================================================
   */
  async updateOrderStatus(
    sellerId,
    orderId,
    status
  ) {
    const order =
      await this.getSellerOrder(
        sellerId,
        orderId
      );

    if (!order) {
      return null;
    }

    /**
     * =================================================
     * VALID ORDER STATUS
     * =================================================
     */

    const allowedStatuses = [
      "Pending",
      "Accepted",
      "Rejected",
      "Shipped",
      "Delivered",
      "Completed",
      "Cancelled",
    ];

    if (!allowedStatuses.includes(status)) {
      throw new Error(
        "Invalid order status."
      );
    }

    /**
     * =================================================
     * PREVENT INVALID TRANSITIONS
     * =================================================
     */

    if (
      order.status === "Cancelled" &&
      status === "Completed"
    ) {
      throw new Error(
        "A cancelled order cannot be completed."
      );
    }

    /**
     * Cannot modify an already completed order
     * back to another status.
     */
    if (
      order.status === "Completed" &&
      status !== "Completed"
    ) {
      throw new Error(
        "A completed order cannot be changed."
      );
    }

    /**
     * =================================================
     * FINANCIAL CHECK
     * =================================================
     *
     * IMPORTANT:
     *
     * Check payment BEFORE saving Completed.
     */

    if (status === "Completed") {
      if (order.paymentStatus !== "Paid") {
        throw new Error(
          "A product order must be paid before revenue can be released."
        );
      }
    }

    /**
     * =================================================
     * MAKE SURE PRODUCTS HAVE SELLER IDs
     * =================================================
     */

    order.products.forEach(
      (product) => {
        if (!product.sellerId) {
          const itemSellerId =
            product.item?.sellerId;

          if (!itemSellerId) {
            return;
          }

          if (
            typeof itemSellerId === "object" &&
            itemSellerId._id
          ) {
            product.sellerId =
              itemSellerId._id;
          } else {
            product.sellerId =
              itemSellerId;
          }
        }
      }
    );

    /**
     * =================================================
     * FINANCIAL RELEASE
     * =================================================
     *
     * Revenue is released only when the order
     * reaches Completed.
     *
     * We do this BEFORE saving the order status.
     */

    if (
      status === "Completed" &&
      order.status !== "Completed"
    ) {
      await revenueService.completeRevenueForOrder(
        order._id
      );
    }

    /**
     * =================================================
     * UPDATE ORDER STATUS
     * =================================================
     */

    order.status = status;

    await order.save();

    return order;
  }
}

export default new SellerOrderService();