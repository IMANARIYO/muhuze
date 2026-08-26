import axios from "axios";

const NOWPAYMENTS_API_URL =
  process.env.NOWPAYMENTS_API_URL ||
  "https://api.nowpayments.io";

const NOWPAYMENTS_API_KEY =
  process.env.NOWPAYMENTS_API_KEY;

class NowPaymentsProvider {
  constructor() {
    this.client = axios.create({
      baseURL: NOWPAYMENTS_API_URL,

      headers: {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json",
      },

      timeout: 15000,
    });
  }

  /**
   * ==========================================
   * CREATE CRYPTO PAYMENT
   * ==========================================
   *
   * MUHUZE prices Premium and marketplace
   * services in USD.
   *
   * The customer pays the applicable
   * NOWPayments processing fee.
   *
   * Example:
   *
   * MUHUZE price = $100
   *
   * NOWPayments calculates the crypto
   * payment amount based on the selected
   * currency/network and applicable fees.
   */

  async createPayment({
    usdAmount,
    payCurrency,
    orderId,
    orderDescription,
    ipnCallbackUrl,
  }) {
    if (!NOWPAYMENTS_API_KEY) {
      throw new Error(
        "NOWPAYMENTS_API_KEY is not configured"
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

    if (!payCurrency) {
      throw new Error(
        "Crypto payment currency is required"
      );
    }

    if (!orderId) {
      throw new Error(
        "Order ID is required"
      );
    }

    const feePaidByUser =
      process.env
        .NOWPAYMENTS_FEE_PAID_BY_USER ===
      "true";

    const paymentPayload = {
      price_amount: usdAmount,

      price_currency: "usd",

      pay_currency: payCurrency,

      order_id: orderId,

      order_description:
        orderDescription ||
        `MUHUZE payment ${orderId}`,

      ipn_callback_url:
        ipnCallbackUrl,
    };

    /**
     * ==========================================
     * CUSTOMER PAYS PROVIDER FEE
     * ==========================================
     *
     * Only send this option when explicitly
     * enabled in the backend environment.
     */

    if (feePaidByUser) {
      paymentPayload.is_fee_paid_by_user =
        true;
    }

    console.log(
      "NOWPayments payment request:",
      {
        priceAmount: usdAmount,
        priceCurrency: "usd",
        payCurrency,
        feePaidByUser,
        orderId,
      }
    );

    const response =
      await this.client.post(
        "/v1/payment",
        paymentPayload
      );
console.log(
  "NOWPayments payment response:",
  response.data
);
    return response.data;
  }

  /**
   * ==========================================
   * GET PAYMENT STATUS
   * ==========================================
   */

  async getPaymentStatus(
    paymentId
  ) {
    if (!paymentId) {
      throw new Error(
        "Payment ID is required"
      );
    }

    const response =
      await this.client.get(
        `/v1/payment/${paymentId}`
      );

    return response.data;
  }

  /**
   * ==========================================
   * GET AVAILABLE CURRENCIES
   * ==========================================
   */

  async getCurrencies() {
    const response =
      await this.client.get(
        "/v1/currencies"
      );

    return response.data;
  }
}

export default new NowPaymentsProvider();