import Payment from "../models/Payment.js";
import Order from "../models/Order.js";
import RevenueTransaction from "../models/RevenueTransaction.js";

import verifyNowPaymentsSignature from "../utils/nowPaymentsSignature.js";

import nowPaymentsProvider from "../providers/nowPaymentsProvider.js";

import revenueService from "./revenueService.js";
import exchangeRateService from "./exchangeRateService.js";
import premiumService from "./premiumService.js";
import referralCommissionService from "./referralCommissionService.js";

class PaymentService {
  /**
   * =====================================================
   * CRYPTO PAYMENT RULES
   * =====================================================
   *
   * MUHUZE supports:
   *
   * USDT + BEP20
   * USDT + ERC20
   * USDC + ERC20
   *
   * USDT + TRC20      NOT SUPPORTED
   * USDC + BEP20      NOT SUPPORTED
   * =====================================================
   */

  getAllowedCryptoNetworks(cryptoCurrency) {
    const allowedCryptoPayments = {
      USDT: [
        "BEP20",
        "ERC20",
      ],

      USDC: [
        "ERC20",
      ],
    };

    return (
      allowedCryptoPayments[
        cryptoCurrency
      ] || []
    );
  }

  /**
   * =====================================================
   * CONVERT MUHUZE CRYPTO SELECTION
   * TO NOWPAYMENTS CURRENCY CODE
   * =====================================================
   */

  getNowPaymentsCurrency(
    cryptoCurrency,
    cryptoNetwork
  ) {
    const currencyMap = {
      "USDT_BEP20": "usdtbsc",
      "USDT_ERC20": "usdterc20",
      "USDC_ERC20": "usdcerc20",
    };

    const key =
      `${cryptoCurrency}_${cryptoNetwork}`;

    const currency =
      currencyMap[key];

    if (!currency) {
      throw new Error(
        `Unsupported crypto payment combination: ${cryptoCurrency} ${cryptoNetwork}`
      );
    }

    return currency;
  }

  /**
   * =====================================================
   * VALIDATE CRYPTO PAYMENT
   * =====================================================
   */

  validateCryptoPayment(
    cryptoCurrency,
    cryptoNetwork
  ) {
    if (!cryptoCurrency) {
      throw new Error(
        "Crypto currency is required"
      );
    }

    if (
      !["USDT", "USDC"].includes(
        cryptoCurrency
      )
    ) {
      throw new Error(
        `Unsupported crypto currency: ${cryptoCurrency}`
      );
    }

    if (!cryptoNetwork) {
      throw new Error(
        "Crypto network is required"
      );
    }

    const allowedNetworks =
      this.getAllowedCryptoNetworks(
        cryptoCurrency
      );

    if (
      !allowedNetworks.includes(
        cryptoNetwork
      )
    ) {
      throw new Error(
        `${cryptoCurrency} is not supported on ${cryptoNetwork}. ` +
          `Supported networks: ${allowedNetworks.join(
            ", "
          )}.`
      );
    }

    return true;
  }

  /**
   * =====================================================
   * GET PAYMENT BY ID
   * =====================================================
   */

  async getPaymentById(paymentId) {
    if (!paymentId) {
      throw new Error(
        "Payment ID is required"
      );
    }

    return await Payment.findById(
      paymentId
    );
  }

  /**
   * =====================================================
   * GET USER PAYMENTS
   * =====================================================
   */

  async getUserPayments(userId) {
    if (!userId) {
      throw new Error(
        "User ID is required"
      );
    }

    return await Payment.find({
      userId,
    }).sort({
      createdAt: -1,
    });
  }

  /**
   * =====================================================
   * FIND PAYMENT BY NOWPAYMENTS ID
   * =====================================================
   */

  async getPaymentByProviderId(
    providerPaymentId
  ) {
    if (!providerPaymentId) {
      throw new Error(
        "Provider payment ID is required"
      );
    }

    return await Payment.findOne({
      providerPaymentId,
    });
  }

  /**
   * =====================================================
   * CREATE PAYMENT
   * =====================================================
   *
   * Flow:
   *
   * MUHUZE
   *    ↓
   * Create Pending Payment
   *    ↓
   * NOWPayments
   *    ↓
   * Save provider payment information
   *
   * Premium is NOT activated here.
   *
   * Premium activation happens only after
   * NOWPayments confirms the payment.
   * =====================================================
   */

  async createPayment({
    userId,
    sourceId,
    sourceType,
    usdAmount,
    paymentMethod,
    cryptoCurrency,
    cryptoNetwork,
    description,
  }) {
    if (!userId) {
      throw new Error(
        "User ID is required"
      );
    }

    if (!sourceId) {
      throw new Error(
        "Payment source ID is required"
      );
    }

    if (!sourceType) {
      throw new Error(
        "Payment source type is required"
      );
    }

    if (
      ![
        "PRODUCT_SALE",
        "PREMIUM",
        "PROMOTION",
        "ADVERTISING",
      ].includes(sourceType)
    ) {
      throw new Error(
        `Unsupported payment source type: ${sourceType}`
      );
    }

    if (
      typeof usdAmount !== "number" ||
      !Number.isFinite(usdAmount) ||
      usdAmount <= 0
    ) {
      throw new Error(
        "Valid USD amount is required"
      );
    }

    if (
      !["CARD", "CRYPTO"].includes(
        paymentMethod
      )
    ) {
      throw new Error(
        "Unsupported payment method"
      );
    }

    /**
     * =================================================
     * CURRENT PAYMENT IMPLEMENTATION
     * =================================================
     *
     * MUHUZE currently uses NOWPayments crypto
     * processing.
     */

    if (paymentMethod !== "CRYPTO") {
      throw new Error(
        "Only crypto payments are currently supported through NOWPayments."
      );
    }

    /**
     * Validate crypto selection.
     */

    this.validateCryptoPayment(
      cryptoCurrency,
      cryptoNetwork
    );

    /**
     * Convert to NOWPayments currency code.
     */

    const payCurrency =
      this.getNowPaymentsCurrency(
        cryptoCurrency,
        cryptoNetwork
      );

    /**
     * =================================================
     * CREATE MUHUZE PAYMENT FIRST
     * =================================================
     *
     * This gives us a permanent internal payment
     * ID which is then used as the NOWPayments order ID.
     */

    const payment =
      await Payment.create({
        userId,

        sourceId,

        sourceType,

        usdAmount,

        paymentMethod,

        cryptoCurrency,

        cryptoNetwork,

        provider:
          "NOWPayments",

        status:
          "Pending",
      });

    try {
      /**
       * =================================================
       * NOWPAYMENTS CALLBACK
       * =================================================
       */

      const ipnCallbackUrl =
        process.env.NOWPAYMENTS_IPN_CALLBACK_URL;

      if (!ipnCallbackUrl) {
        throw new Error(
          "NOWPAYMENTS_IPN_CALLBACK_URL is not configured"
        );
      }

      /**
       * =================================================
       * CREATE NOWPAYMENTS PAYMENT
       * =================================================
       */

      const providerPayment =
        await nowPaymentsProvider.createPayment(
          {
            usdAmount,

            payCurrency,

            orderId:
              payment._id.toString(),

            orderDescription:
              description ||
              `MUHUZE ${sourceType} payment`,

            ipnCallbackUrl,
          }
        );

      /**
       * =================================================
       * SAVE PROVIDER INFORMATION
       * =================================================
       */

      payment.providerPaymentId =
        providerPayment.payment_id
          ? String(
              providerPayment.payment_id
            )
          : undefined;

      payment.cryptoAmount =
        providerPayment.pay_amount;

      /**
       * The provider may return the actual
       * payment address.
       */

      payment.walletAddress =
        providerPayment.pay_address;

      /**
       * Save provider information.
       */

      await payment.save();

      return {
        payment,

        provider: providerPayment,
      };
    } catch (error) {
      /**
       * =================================================
       * PROVIDER CREATION FAILED
       * =================================================
       *
       * Keep the payment record for audit purposes,
       * but mark it as Failed.
       */

      payment.status = "Failed";

      await payment.save();

      throw error;
    }
  }

  /**
   * =====================================================
   * MAP NOWPAYMENTS STATUS
   * =====================================================
   */

  mapNowPaymentsStatus(
    providerStatus
  ) {
    const status =
      String(
        providerStatus || ""
      ).toLowerCase();

    switch (status) {
      case "waiting":
        return "Pending";

      case "confirming":
        return "Processing";

      case "confirmed":
      case "finished":
        return "Confirmed";

      case "sending":
        return "Processing";

      case "partially_paid":
        return "PartiallyPaid";

      case "failed":
        return "Failed";

      case "refunded":
        return "Refunded";

      case "expired":
        return "Cancelled";

      default:
        return "Processing";
    }
  }

  /**
   * =====================================================
   * UPDATE PAYMENT STATUS
   * =====================================================
   *
   * This is the central payment-status handler.
   * =====================================================
   */

  async updatePaymentStatus(
    payment,
    providerData
  ) {
    if (!payment) {
      throw new Error(
        "Payment is required"
      );
    }

    if (!providerData) {
      throw new Error(
        "Provider payment data is required"
      );
    }

    const mappedStatus =
      this.mapNowPaymentsStatus(
        providerData.payment_status
      );

    /**
     * =================================================
     * IDEMPOTENCY
     * =================================================
     *
     * A repeated confirmed webhook must not
     * activate Premium twice or create revenue twice.
     */

    const updateData = {
      status: mappedStatus,
    };

    if (
      providerData.txid
    ) {
      updateData.transactionHash =
        providerData.txid;
    }

    if (
      providerData.pay_amount
    ) {
      updateData.cryptoAmount =
        providerData.pay_amount;
    }

    if (
      providerData.pay_address
    ) {
      updateData.walletAddress =
        providerData.pay_address;
    }

    if (
      mappedStatus ===
      "Confirmed"
    ) {
      updateData.confirmedAt =
        payment.confirmedAt ||
        new Date();
    }

    if (
      mappedStatus ===
      "Refunded"
    ) {
      updateData.refundedAt =
        new Date();
    }

    const updatedPayment =
      await Payment.findByIdAndUpdate(
        payment._id,
        updateData,
        {
          returnDocument:
            "after",

          runValidators: true,
        }
      );

    /**
     * =================================================
     * CONFIRMED PAYMENT
     * =================================================
     */

    if (
      mappedStatus ===
      "Confirmed"
    ) {
      await this.processConfirmedPayment(
        payment,
        updatedPayment
      );
    }

    return updatedPayment;
  }

  /**
   * =====================================================
   * PROCESS CONFIRMED PAYMENT
   * =====================================================
   *
   * PREMIUM:
   *
   * Confirmed
   *    ↓
   * Premium activated
   *    ↓
   * Premium revenue immediately available
   *    ↓
   * Referral commission immediately available
   *
   *
   * PRODUCT:
   *
   * Confirmed
   *    ↓
   * Order Paid
   *    ↓
   * Revenue Pending
   *    ↓
   * Order Completed
   *    ↓
   * Revenue Completed
   *    ↓
   * Referral commission available
   * =====================================================
   */

  async processConfirmedPayment(
    payment,
    updatedPayment
  ) {
    if (!payment) {
      throw new Error(
        "Payment is required"
      );
    }

    /**
     * =================================================
     * PREMIUM MEMBERSHIP
     * =================================================
     */

    if (
      payment.sourceType ===
      "PREMIUM"
    ) {
      /**
       * Activate Premium.
       */

      await premiumService.activateFromPayment(
        payment._id
      );

      /**
       * =================================================
       * PREMIUM REVENUE
       * =================================================
       *
       * Premium membership is not a product order.
       * There is no delivery/refund waiting period
       * in this financial flow.
       *
       * Therefore the revenue becomes Completed
       * immediately after confirmed payment.
       */

      let revenueTransaction =
        await RevenueTransaction.findOne({
          sourceId:
            payment.sourceId,

          sourceType:
            "PREMIUM",
        });

      /**
       * Prevent duplicate Premium revenue.
       */

      if (!revenueTransaction) {
        revenueTransaction =
          await RevenueTransaction.create(
            {
              userId:
                payment.userId,

              sourceId:
                payment.sourceId,

              sourceType:
                "PREMIUM",

              sourceAmount:
                payment.usdAmount,

              sourceCurrency:
                "USD",

              exchangeRate:
                1,

              accountingAmount:
                payment.usdAmount,

              accountingCurrency:
                "USD",

              revenueRate:
                100,

              revenueAmount:
                payment.usdAmount,

              referralEligible:
                true,

              status:
                "Completed",

              availableAt:
                new Date(),
            }
          );
      }

      /**
       * =================================================
       * RELEASE PREMIUM REFERRAL COMMISSIONS
       * =================================================
       *
       * Referral pool:
       * 20% of eligible MUHUZE revenue
       *
       * L1 = 12%
       * L2 = 5%
       * L3 = 3%
       */

      if (
        revenueTransaction.referralEligible
      ) {
        await referralCommissionService.processReferralCommissions(
          revenueTransaction._id
        );
      }

      return;
    }

    /**
     * =================================================
     * PRODUCT SALE
     * =================================================
     */

    if (
      payment.sourceType !==
      "PRODUCT_SALE"
    ) {
      return;
    }

    /**
     * =================================================
     * FIND ORDER
     * =================================================
     */

    const order =
      await Order.findById(
        payment.sourceId
      );

    if (!order) {
      throw new Error(
        "Related MUHUZE order not found"
      );
    }

    /**
     * =================================================
     * MARK ORDER AS PAID
     * =================================================
     */

    if (
      order.paymentStatus !==
      "Paid"
    ) {
      order.paymentStatus =
        "Paid";

      await order.save();
    }

    /**
     * =================================================
     * CHECK EXISTING REVENUE
     * =================================================
     */

    let revenueTransaction =
      await revenueService.getRevenueTransactionBySource(
        order._id,
        "PRODUCT_SALE"
      );

    /**
     * =================================================
     * CREATE REVENUE ONLY ONCE
     * =================================================
     *
     * IMPORTANT:
     *
     * Product revenue remains Pending.
     *
     * We do NOT complete the revenue here.
     */

    if (!revenueTransaction) {
      revenueTransaction =
        await revenueService.createProductSaleRevenue(
          {
            order,

            sourceCurrency:
              "RWF",
          }
        );
    }

    /**
     * Do NOT release revenue here.
     *
     * The order must first reach:
     *
     * Delivered → Completed
     *
     * Then SellerOrderService calls:
     *
     * revenueService.completeRevenueForOrder()
     */

    return;
  }

  /**
   * =====================================================
   * PROCESS NOWPAYMENTS IPN
   * =====================================================
   *
   * This endpoint receives the payment status
   * notification from NOWPayments.
   *
   * Signature is verified before processing.
   * =====================================================
   */

  async processNowPaymentsIPN(
    payload,
    receivedSignature
  ) {
    if (!payload) {
      throw new Error(
        "NOWPayments payload is required"
      );
    }

    /**
     * =================================================
     * VERIFY SIGNATURE
     * =================================================
     */

    const validSignature =
      verifyNowPaymentsSignature(
        payload,
        receivedSignature
      );

    if (!validSignature) {
      throw new Error(
        "Invalid NOWPayments IPN signature"
      );
    }

    /**
     * =================================================
     * GET PROVIDER PAYMENT ID
     * =================================================
     */

    const providerPaymentId =
      payload.payment_id
        ? String(
            payload.payment_id
          )
        : null;

    /**
     * =================================================
     * FIND PAYMENT
     * =================================================
     */

    let payment = null;

    if (
      providerPaymentId
    ) {
      payment =
        await this.getPaymentByProviderId(
          providerPaymentId
        );
    }

    /**
     * Fallback:
     *
     * NOWPayments order_id contains our internal
     * MUHUZE Payment ID.
     */

    if (
      !payment &&
      payload.order_id
    ) {
      payment =
        await this.getPaymentById(
          payload.order_id
        );
    }

    if (!payment) {
      throw new Error(
        "MUHUZE payment associated with NOWPayments notification was not found"
      );
    }

    /**
     * =================================================
     * UPDATE PAYMENT
     * =================================================
     */

    return await this.updatePaymentStatus(
      payment,
      payload
    );
  }

  /**
   * =====================================================
   * CHECK LIVE NOWPAYMENTS PAYMENT STATUS
   * =====================================================
   *
   * Used when the customer clicks:
   *
   * "Check Payment Status"
   *
   * This does NOT create a new payment.
   * =====================================================
   */

  async checkPaymentStatus(
    paymentId
  ) {
    if (!paymentId) {
      throw new Error(
        "Payment ID is required"
      );
    }

    const payment =
      await this.getPaymentById(
        paymentId
      );

    if (!payment) {
      throw new Error(
        "Payment not found"
      );
    }

    if (
      !payment.providerPaymentId
    ) {
      throw new Error(
        "NOWPayments payment ID is not available yet"
      );
    }

    /**
     * =================================================
     * GET LIVE PROVIDER STATUS
     * =================================================
     */

    const providerData =
      await nowPaymentsProvider.getPaymentStatus(
        payment.providerPaymentId
      );

    /**
     * =================================================
     * UPDATE MUHUZE PAYMENT
     * =================================================
     */

    return await this.updatePaymentStatus(
      payment,
      providerData
    );
  }
}

export default new PaymentService();