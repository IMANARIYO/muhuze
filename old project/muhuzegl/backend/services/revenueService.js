import RevenueTransaction from "../models/RevenueTransaction.js";
import User from "../models/User.js";
import exchangeRateService from "./exchangeRateService.js";
import referralCommissionService from "./referralCommissionService.js";

/**
 * =====================================================
 * MUHUZE REVENUE SERVICE
 * =====================================================
 *
 * FINANCIAL RULES
 *
 * -----------------------------------------------------
 * PRODUCT SALES
 * -----------------------------------------------------
 *
 * FREE SELLER     → 12%
 * PREMIUM SELLER  → 7%
 *
 * Product revenue is initially Pending.
 *
 * Payment confirmation DOES NOT release revenue.
 *
 * Revenue becomes Completed only when the order
 * reaches the final Completed state.
 *
 * -----------------------------------------------------
 * PREMIUM MEMBERSHIP
 * -----------------------------------------------------
 *
 * Premium payment revenue is available immediately
 * after the payment is confirmed.
 *
 * -----------------------------------------------------
 * REFERRAL PROGRAM
 * -----------------------------------------------------
 *
 * Referral pool = 20% of eligible MUHUZE revenue
 *
 * Level 1 → 12%
 * Level 2 → 5%
 * Level 3 → 3%
 *
 * Premium revenue commissions are immediately
 * available.
 *
 * Product-sale commissions become available only
 * after the product order is completed.
 * =====================================================
 */

class RevenueService {
  // ===================================================
  // SELLER COMMISSION RATES
  // ===================================================

  FREE_SELLER_RATE = 12;

  PREMIUM_SELLER_RATE = 7;

  // ===================================================
  // REFERRAL POOL
  // ===================================================

  REFERRAL_POOL_RATE = 20;

  // ===================================================
  // REFERRAL LEVEL RATES
  // ===================================================

  REFERRAL_COMMISSION_RATES = {
    1: 12,
    2: 5,
    3: 3,
  };

  // ===================================================
  // GET SELLER COMMISSION RATE
  // ===================================================
  //
  // Determines whether the seller currently has
  // an active Premium membership.
  //
  // FREE seller    → 12%
  // PREMIUM seller → 7%
  // ===================================================

  async getSellerCommissionRate(sellerId) {
    if (!sellerId) {
      throw new Error(
        "Seller ID is required"
      );
    }

    const seller =
      await User.findById(sellerId).select(
        "premium"
      );

    if (!seller) {
      throw new Error(
        `Seller ${sellerId} not found`
      );
    }

    const premium =
      seller.premium;

    const premiumActive =
      premium?.active === true &&
      premium?.expiryDate &&
      new Date(premium.expiryDate) >
        new Date();

    return premiumActive
      ? this.PREMIUM_SELLER_RATE
      : this.FREE_SELLER_RATE;
  }

  // ===================================================
  // CALCULATE PRODUCT SALE REVENUE
  // ===================================================
  //
  // Calculates MUHUZE revenue seller-by-seller.
  //
  // This is important because one order may contain
  // products from different sellers.
  //
  // Example:
  //
  // Seller A = Free → 12%
  // Seller B = Premium → 7%
  // ===================================================

  async calculateProductSaleRevenue(order) {
    if (!order) {
      throw new Error(
        "Order is required"
      );
    }

    if (
      !order.products ||
      order.products.length === 0
    ) {
      throw new Error(
        "Order contains no products"
      );
    }

    let totalOrderAmountRwf = 0;
    let totalRevenueRwf = 0;

    const sellerBreakdown = [];

    for (
      const product of order.products
    ) {
      // -----------------------------------------------
      // SELLER
      // -----------------------------------------------

      let sellerId =
        product.sellerId;

      // Support older orders where sellerId may
      // still exist inside product.item.
      if (!sellerId) {
        sellerId =
          product.item?.sellerId;
      }

      // Handle populated seller object.
      if (
        sellerId &&
        typeof sellerId === "object" &&
        sellerId._id
      ) {
        sellerId =
          sellerId._id;
      }

      if (!sellerId) {
        throw new Error(
          "Order product is missing sellerId"
        );
      }

      // -----------------------------------------------
      // PRODUCT ITEM
      // -----------------------------------------------

      const item =
        product.item;

      if (!item) {
        throw new Error(
          "Order product item is missing"
        );
      }

      // -----------------------------------------------
      // PRICE
      // -----------------------------------------------

      const price =
        Number(item.price);

      if (
        !Number.isFinite(price) ||
        price < 0
      ) {
        throw new Error(
          "Invalid product price in order"
        );
      }

      // -----------------------------------------------
      // QUANTITY
      // -----------------------------------------------

      const quantity =
        Number(product.quantity) || 1;

      if (quantity <= 0) {
        throw new Error(
          "Invalid product quantity"
        );
      }

      // -----------------------------------------------
      // LINE TOTAL
      // -----------------------------------------------

      const lineTotal =
        price * quantity;

      // -----------------------------------------------
      // SELLER COMMISSION RATE
      // -----------------------------------------------

      const commissionRate =
        await this.getSellerCommissionRate(
          sellerId
        );

      // -----------------------------------------------
      // MUHUZE REVENUE
      // -----------------------------------------------

      const revenueAmount =
        (lineTotal * commissionRate) /
        100;

      totalOrderAmountRwf +=
        lineTotal;

      totalRevenueRwf +=
        revenueAmount;

     const sellerEarning =
  lineTotal - revenueAmount;

sellerBreakdown.push({
  sellerId,

  lineAmount:
    Number(lineTotal.toFixed(2)),

  commissionRate,

  revenueAmount:
    Number(revenueAmount.toFixed(2)),

  sellerEarning:
    Number(sellerEarning.toFixed(2)),
});
    }

    if (
      totalOrderAmountRwf <= 0
    ) {
      throw new Error(
        "Invalid order amount"
      );
    }

    return {
      totalOrderAmountRwf,

      totalRevenueRwf,

      sellerBreakdown,
    };
  }

  // ===================================================
  // CREATE PRODUCT SALE REVENUE
  // ===================================================
  //
  // Product revenue starts as Pending.
  //
  // Payment confirmation does NOT make it available.
  // ===================================================

  async createProductSaleRevenue({
    order,
    sourceCurrency = "RWF",
  }) {
    if (!order) {
      throw new Error(
        "Order is required"
      );
    }

    if (!order._id) {
      throw new Error(
        "Order ID is required"
      );
    }

    if (!order.buyerId) {
      throw new Error(
        "Order buyer is required"
      );
    }

    // =================================================
    // DUPLICATE PROTECTION
    // =================================================

    const existing =
      await this.getRevenueTransactionBySource(
        order._id,
        "PRODUCT_SALE"
      );

    if (existing) {
      return existing;
    }

    // =================================================
    // LIVE EXCHANGE RATE
    // =================================================

    const exchangeRate =
      await exchangeRateService.getUsdToRwfRate();

    if (
      !exchangeRate ||
      exchangeRate <= 0
    ) {
      throw new Error(
        "Invalid USD to RWF exchange rate"
      );
    }

    // =================================================
    // CALCULATE SELLER REVENUE
    // =================================================

    const {
      totalOrderAmountRwf,
      totalRevenueRwf,
      sellerBreakdown,
    } =
      await this.calculateProductSaleRevenue(
        order
      );

    // =================================================
    // CONVERT TO USD
    // =================================================

    const accountingAmount =
      totalOrderAmountRwf /
      exchangeRate;

    const accountingRevenueAmount =
      totalRevenueRwf /
      exchangeRate;

    // =================================================
    // EFFECTIVE REVENUE RATE
    // =================================================
    //
    // Useful when an order contains both free and
    // Premium sellers.
    // =================================================

    const revenueRate =
      totalOrderAmountRwf > 0
        ? (
            totalRevenueRwf /
            totalOrderAmountRwf
          ) * 100
        : 0;

    // =================================================
    // CREATE REVENUE TRANSACTION
    // =================================================

    const revenueTransaction =
      await RevenueTransaction.create({
        userId:
          order.buyerId,

        sourceId:
          order._id,

        sourceType:
          "PRODUCT_SALE",

        sourceAmount:
          totalOrderAmountRwf,

        sourceCurrency,

        exchangeRate,

        accountingAmount,

        accountingCurrency:
          "USD",

        revenueRate:
          Number(
            revenueRate.toFixed(4)
          ),

        revenueAmount:
          Number(
            accountingRevenueAmount.toFixed(2)
          ),

        referralEligible:
          true,

        // IMPORTANT:
        // Product revenue waits for order completion.
        status:
          "Pending",

        availableAt:
          null,
      });

    console.log(
      "MUHUZE product revenue created:",
      {
        orderId:
          order._id.toString(),

        totalOrderAmountRwf,

        totalRevenueRwf,

        accountingRevenueAmount,

        sellerBreakdown,
      }
    );

    return revenueTransaction;
  }

  // ===================================================
  // CREATE PREMIUM REVENUE
  // ===================================================
  //
  // Premium membership revenue is different from
  // product-sale revenue.
  //
  // Premium payment is confirmed by the payment
  // provider before this function is called.
  //
  // Therefore Premium revenue becomes Completed
  // immediately.
  // ===================================================

  async createPremiumRevenue({
    payment,
    subscription,
  }) {
    if (!payment) {
      throw new Error(
        "Premium payment is required"
      );
    }

    if (!payment._id) {
      throw new Error(
        "Premium payment ID is required"
      );
    }

    if (!payment.userId) {
      throw new Error(
        "Premium payment user is required"
      );
    }

    if (
      payment.sourceType !==
      "PREMIUM"
    ) {
      throw new Error(
        "Payment is not a Premium payment"
      );
    }

    if (
      payment.status !==
      "Confirmed"
    ) {
      throw new Error(
        "Premium revenue cannot be created before payment confirmation"
      );
    }

    if (
      !payment.usdAmount ||
      payment.usdAmount <= 0
    ) {
      throw new Error(
        "Invalid Premium payment amount"
      );
    }

    // =================================================
    // DUPLICATE PROTECTION
    // =================================================

    const existing =
      await this.getRevenueTransactionBySource(
        payment._id,
        "PREMIUM"
      );

    if (existing) {
      return existing;
    }

    // =================================================
    // PREMIUM PAYMENT IS ALREADY USD
    // =================================================

    const accountingAmount =
      Number(
        payment.usdAmount
      );

    // =================================================
    // PREMIUM REVENUE
    // =================================================
    //
    // The Premium membership payment is MUHUZE
    // revenue, therefore the current revenue rate
    // is 100%.
    // =================================================

    const revenueAmount =
      accountingAmount;

    // =================================================
    // CREATE COMPLETED REVENUE
    // =================================================

    const revenueTransaction =
      await RevenueTransaction.create({
        userId:
          payment.userId,

        sourceId:
          payment._id,

        sourceType:
          "PREMIUM",

        sourceAmount:
          accountingAmount,

        sourceCurrency:
          "USD",

        exchangeRate:
          1,

        accountingAmount,

        accountingCurrency:
          "USD",

        revenueRate:
          100,

        revenueAmount,

        referralEligible:
          true,

        // PREMIUM IS IMMEDIATELY AVAILABLE
        status:
          "Completed",

        availableAt:
          new Date(),
      });

    console.log(
      "MUHUZE Premium revenue created:",
      {
        paymentId:
          payment._id.toString(),

        subscriptionId:
          subscription?._id?.toString(),

        revenueAmount,
      }
    );

    // =================================================
    // IMMEDIATE REFERRAL COMMISSION
    // =================================================

    if (
      revenueTransaction.referralEligible
    ) {
      await referralCommissionService.processReferralCommissions(
        revenueTransaction._id
      );
    }

    return revenueTransaction;
  }

  // ===================================================
  // FIND REVENUE BY SOURCE
  // ===================================================

  async getRevenueTransactionBySource(
    sourceId,
    sourceType
  ) {
    if (!sourceId) {
      throw new Error(
        "Revenue source ID is required"
      );
    }

    if (!sourceType) {
      throw new Error(
        "Revenue source type is required"
      );
    }

    return await RevenueTransaction.findOne({
      sourceId,
      sourceType,
    });
  }

  // ===================================================
  // GET ONE REVENUE TRANSACTION
  // ===================================================

  async getRevenueTransaction(
    id
  ) {
    if (!id) {
      throw new Error(
        "Revenue transaction ID is required"
      );
    }

    return await RevenueTransaction.findById(
      id
    );
  }

  // ===================================================
  // COMPLETE REVENUE TRANSACTION
  // ===================================================
  //
  // Used primarily for PRODUCT_SALE.
  //
  // Pending → Completed
  //
  // Once completed, referral commissions are
  // generated.
  // ===================================================

  async completeRevenueTransaction(
    revenueTransactionId
  ) {
    if (!revenueTransactionId) {
      throw new Error(
        "Revenue transaction ID is required"
      );
    }

    const revenueTransaction =
      await RevenueTransaction.findById(
        revenueTransactionId
      );

    if (!revenueTransaction) {
      throw new Error(
        "Revenue transaction not found"
      );
    }

    // =================================================
    // IDEMPOTENCY
    // =================================================

    if (
      revenueTransaction.status ===
      "Completed"
    ) {
      return revenueTransaction;
    }

    if (
      revenueTransaction.status !==
      "Pending"
    ) {
      throw new Error(
        `Revenue transaction cannot be completed because it is ${revenueTransaction.status}.`
      );
    }

    // =================================================
    // COMPLETE REVENUE
    // =================================================

    revenueTransaction.status =
      "Completed";

    revenueTransaction.availableAt =
      new Date();

    await revenueTransaction.save();

    // =================================================
    // CREATE REFERRAL COMMISSIONS
    // =================================================

    if (
      revenueTransaction.referralEligible
    ) {
      await referralCommissionService.processReferralCommissions(
        revenueTransaction._id
      );
    }

    return revenueTransaction;
  }

  // ===================================================
  // COMPLETE REVENUE FOR ORDER
  // ===================================================
  //
  // Called when:
  //
  // Order → Completed
  //
  // This is the financial release point for product
  // sales.
  // ===================================================

  async completeRevenueForOrder(
    orderId
  ) {
    if (!orderId) {
      throw new Error(
        "Order ID is required"
      );
    }

    const revenueTransaction =
      await this.getRevenueTransactionBySource(
        orderId,
        "PRODUCT_SALE"
      );

    if (!revenueTransaction) {
      throw new Error(
        "Product-sale revenue transaction not found for this order"
      );
    }

    return await this.completeRevenueTransaction(
      revenueTransaction._id
    );
  }

  // ===================================================
  // GET USER REVENUE
  // ===================================================

  async getUserRevenue(
    userId
  ) {
    if (!userId) {
      throw new Error(
        "User ID is required"
      );
    }

    return await RevenueTransaction.find({
      userId,
    }).sort({
      createdAt: -1,
    });
  }
}

export default new RevenueService();