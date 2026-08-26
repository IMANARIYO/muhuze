import axios from "axios";

const EXCHANGE_RATE_API =
  "https://open.er-api.com/v6/latest/USD";

class ExchangeRateService {
  /**
   * Get the current USD → RWF exchange rate.
   *
   * Returns:
   * 1 USD = X RWF
   */
  async getUsdToRwfRate() {
    const response = await axios.get(
      EXCHANGE_RATE_API,
      {
        timeout: 10000,
      }
    );

    const rates = response.data?.rates;

    if (!rates || !rates.RWF) {
      throw new Error(
        "USD to RWF exchange rate unavailable"
      );
    }

    const rate = Number(rates.RWF);

    if (!rate || rate <= 0) {
      throw new Error(
        "Invalid USD to RWF exchange rate"
      );
    }

    return rate;
  }
}

export default new ExchangeRateService();