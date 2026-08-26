import mongoose from "mongoose";

import Order from "../models/Order.js";
import Marketplace from "../models/Marketplace.js";
import User from "../models/User.js";
import RevenueTransaction from "../models/RevenueTransaction.js";

import walletService from "./walletService.js";
import currencyService from "./currencyService.js";
class OrderService {
  /**
   * ==========================================
   * CREATE ORDER
   * ==========================================
   *
   * The client sends:
   *
   * products: [
   *   {
   *     productId,
   *     quantity
   *   }
   * ]
   *
   * The backend gets the real Marketplace
   * listing and stores the price at purchase.
   */
  async createOrder(data) {
    const {
      buyerId,
      buyer,
      products,
      deliveryAddress,
      paymentMethod,
    } = data;

    /**
     * Validate buyer ID
     */
    if (!mongoose.Types.ObjectId.isValid(buyerId)) {
      throw new Error("Invalid buyer ID.");
    }

    /**
     * Validate products
     */
    if (!Array.isArray(products) || products.length === 0) {
      throw new Error(
        "Order must contain at least one product."
      );
    }

    /**
     * Validate delivery address
     */
    if (!deliveryAddress?.trim()) {
      throw new Error(
        "Delivery address is required."
      );
    }

    /**
     * Validate payment method
     */
    if (!paymentMethod?.trim()) {
      throw new Error(
        "Payment method is required."
      );
    }

    const orderProducts = [];

    let total = 0;

    /**
     * ==========================================
     * PROCESS EACH PRODUCT
     * ==========================================
     */

    for (const product of products) {
      const { productId } = product;

      const quantity = Number(
        product.quantity || 1
      );

      /**
       * Validate product ID
       */
      if (
        !mongoose.Types.ObjectId.isValid(
          productId
        )
      ) {
        throw new Error(
          "Invalid product ID."
        );
      }

      /**
       * Validate quantity
       */
      if (
        !Number.isInteger(quantity) ||
        quantity <= 0
      ) {
        throw new Error(
          "Product quantity must be greater than zero."
        );
      }

      /**
       * Find marketplace listing
       */
      const listing =
        await Marketplace.findOne({
          _id: productId,
          status: "published",
        });

      if (!listing) {
        throw new Error(
          `Marketplace product ${productId} is not available.`
        );
      }

      /**
       * Get current marketplace price
       *
       * This becomes the permanent
       * priceAtPurchase in the order.
       */
      const price = Number(
        listing.price
      );

      /**
       * Calculate subtotal
       */
      const subtotal = Number(
        (
          price * quantity
        ).toFixed(2)
      );

      /**
       * Add to order total
       */
      total += subtotal;

      /**
       * Store a snapshot of the product
       * inside the order.
       */
      orderProducts.push({
        productId:
          listing._id,

        sellerId:
          listing.sellerId,

        title:
          listing.title,

        priceAtPurchase:
          price,

        quantity,

        subtotal,

        currency:
          listing.currency,
      });
    }

    /**
     * Round total
     */
    total = Number(
      total.toFixed(2)
    );

    /**
     * ==========================================
     * CREATE ORDER
     * ==========================================
     */

    return await Order.create({
      buyerId,

      buyer,

      products:
        orderProducts,

      total,

      deliveryAddress:
        deliveryAddress.trim(),

      paymentMethod:
        paymentMethod.trim(),

      status:
        "Pending",

      paymentStatus:
        "Pending",
    });
  }
/**
 * ==========================================
 * COMPLETE ORDER
 * ==========================================
 *
 * Financial flow:
 *
 * Order
 *   ↓
 * RevenueTransaction
 *   ↓
 * Seller Wallet
 *
 * Premium seller:
 *   MUHUZE = 7%
 *   Seller = 93%
 *
 * Non-Premium seller:
 *   MUHUZE = 12%
 *   Seller = 88%
 */

async completeOrder(id) {
  if (!mongoose.Types.ObjectId.isValid(id)) {
    throw new Error("Invalid order ID.");
  }

  const session =
    await mongoose.startSession();

  try {
    let completedOrder;

    await session.withTransaction(
      async () => {
        /**
         * ==========================================
         * FIND ORDER
         * ==========================================
         */

        const order =
          await Order.findById(id)
            .session(session);

        if (!order) {
          throw new Error(
            "Order not found."
          );
        }

        /**
         * ==========================================
         * PREVENT DUPLICATE COMPLETION
         * ==========================================
         */

        if (
          order.status === "Completed"
        ) {
          completedOrder = order;
          return;
        }

        /**
         * ==========================================
         * PAYMENT MUST BE PAID
         * ==========================================
         */

        if (
          order.paymentStatus !== "Paid"
        ) {
          throw new Error(
            "Order cannot be completed because payment has not been confirmed."
          );
        }

        /**
         * ==========================================
         * ORDER MUST BE DELIVERED
         * ==========================================
         */

        if (
          order.status !== "Delivered"
        ) {
          throw new Error(
            `Order cannot be completed because its current status is ${order.status}.`
          );
        }

        /**
         * ==========================================
         * VALIDATE PRODUCTS
         * ==========================================
         */

        if (
          !Array.isArray(order.products) ||
          order.products.length === 0
        ) {
          throw new Error(
            "Order contains no products."
          );
        }

        /**
         * ==========================================
         * SELLER BREAKDOWN
         * ==========================================
         */

        const sellerBreakdown = [];

        let totalRevenue = 0;

        /**
         * ==========================================
         * PROCESS EACH ORDER ITEM
         * ==========================================
         */

        for (
          const item of order.products
        ) {
          /**
           * Find seller.
           */

          const seller =
            await User.findById(
              item.sellerId
            ).session(session);

          if (!seller) {
            throw new Error(
              `Seller ${item.sellerId} not found.`
            );
          }

        
const commissionRate =
  seller.premium?.active === true
    ? 7
    : 12;

          /**
           * ========================================
           * LINE AMOUNT
           * ========================================
           */

          const lineAmount =
            Number(
              item.subtotal.toFixed(2)
            );

          /**
           * ========================================
           * MUHUZE REVENUE
           * ========================================
           */

          const revenueAmount =
            Number(
              (
                lineAmount *
                (commissionRate / 100)
              ).toFixed(2)
            );

          /**
           * ========================================
           * SELLER EARNING
           * ========================================
           */

          const sellerEarning =
            Number(
              (
                lineAmount -
                revenueAmount
              ).toFixed(2)
            );

          totalRevenue +=
            revenueAmount;

          /**
           * ========================================
           * STORE SELLER BREAKDOWN
           * ========================================
           */

          sellerBreakdown.push({
            sellerId:
              seller._id,

            lineAmount,

            commissionRate,

            revenueAmount,

            sellerEarning,
          });
        }

        /**
         * Round total MUHUZE revenue.
         */

        totalRevenue =
          Number(
            totalRevenue.toFixed(2)
          );

        /**
         * ==========================================
         * CURRENCY
         * ==========================================
         *
         * For the first financial test,
         * the order must use one currency.
         */

        const sourceCurrency =
          order.products[0].currency;

        const mixedCurrency =
          order.products.some(
            (item) =>
              item.currency !==
              sourceCurrency
          );

        if (mixedCurrency) {
          throw new Error(
            "An order cannot contain multiple currencies."
          );
        }

        const revenueRate =
  order.total > 0
    ? Number(
        (
          (totalRevenue /
            order.total) *
          100
        ).toFixed(2)
      )
    : 0;

/**
 * ==========================================
 * CURRENCY CONVERSION
 * ==========================================
 *
 * The order keeps its original payment
 * currency.
 *
 * accountingAmount is the USD equivalent.
 */

const accountingCurrency = "USD";

const accountingAmount =
  await currencyService.convertToUsd(
    order.total,
    sourceCurrency
  );

const accountingRevenueAmount =
  await currencyService.convertToUsd(
    totalRevenue,
    sourceCurrency
  );

/**
 * ==========================================
 * CREATE REVENUE TRANSACTION
 * ==========================================
 */

const revenueTransactions =
  await RevenueTransaction.create(
    [
      {
        userId:
          order.buyerId,

        sourceId:
          order._id,

        sourceType:
          "PRODUCT_SALE",

        /**
         * Original customer payment
         */
        sourceAmount:
          order.total,

        sourceCurrency:
          sourceCurrency,

        /**
         * Actual exchange rate used
         */
        exchangeRate:
          accountingAmount /
          order.total,

        /**
         * MUHUZE internal accounting
         */
        accountingAmount:
          accountingAmount,

        accountingCurrency:
          accountingCurrency,

        revenueRate,

        /**
         * MUHUZE revenue in USD
         * for internal accounting.
         */
        revenueAmount:
          accountingRevenueAmount,

        sellerBreakdown,

        referralEligible:
          true,

        status:
          "Completed",

        availableAt:
          new Date(),
      },
    ],
    {
      session,
    }
  );

        const revenueTransaction =
          revenueTransactions[0];

        /**
         * ==========================================
         * CREDIT SELLERS
         * ==========================================
         */

        for (
          const breakdown
          of sellerBreakdown
        ) {
         await walletService.creditSellerRevenue(
  breakdown.sellerId,
  breakdown.sellerEarning,
  revenueTransaction._id,
  sourceCurrency,
  session
);
        }

        /**
         * ==========================================
         * MARK ORDER COMPLETED
         * ==========================================
         */

        order.status =
          "Completed";

        await order.save({
          session,
        });

        completedOrder =
          order;
      }
    );

    return completedOrder;

  } finally {
    await session.endSession();
  }
}
  /**
   * ==========================================
   * GET ALL ORDERS
   * ==========================================
   */

  async getAllOrders() {
    return await Order.find()
      .sort({
        createdAt: -1,
      });
  }

  /**
   * ==========================================
   * GET ORDER BY ID
   * ==========================================
   */

  async getOrderById(id) {
    return await Order.findById(id);
  }

  /**
   * ==========================================
   * BUYER ORDERS
   * ==========================================
   */

  async getBuyerOrders(
    buyerId
  ) {
    return await Order.find({
      buyerId,
    }).sort({
      createdAt: -1,
    });
  }

  /**
   * ==========================================
   * UPDATE ORDER
   * ==========================================
   */

  async updateOrder(
    id,
    data
  ) {
    return await Order.findByIdAndUpdate(
      id,
      data,
      {
        new: true,
        runValidators: true,
      }
    );
  }

  /**
   * ==========================================
   * DELETE ORDER
   * ==========================================
   */

  async deleteOrder(id) {
    return await Order.findByIdAndDelete(
      id
    );
  }
}

export default new OrderService();