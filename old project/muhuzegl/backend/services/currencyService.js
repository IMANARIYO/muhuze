import exchangeRateService from "./exchangeRateService.js";

/**
 * ============================================================
 * MUHUZE CURRENCY SERVICE
 * ============================================================
 *
 * Purpose:
 * - Convert between MUHUZE supported currencies
 * - Provide USD-equivalent values
 * - Keep wallet balances in their original currencies
 *
 * Supported:
 * RWF
 * USD
 * USDT
 * USDC
 * BTC
 */

const SUPPORTED_CURRENCIES = [
  "RWF",
  "USD",
  "USDT",
  "USDC",
  "BTC",
];

/**
 * ============================================================
 * NORMALIZE CURRENCY
 * ============================================================
 */

const normalizeCurrency = (currency) => {
  if (!currency) {
    throw new Error("Currency is required.");
  }

  const normalized = String(currency)
    .trim()
    .toUpperCase();

  if (
    !SUPPORTED_CURRENCIES.includes(
      normalized
    )
  ) {
    throw new Error(
      `Unsupported currency: ${normalized}`
    );
  }

  return normalized;
};

/**
 * ============================================================
 * VALIDATE AMOUNT
 * ============================================================
 */

const validateAmount = (amount) => {
  const numericAmount = Number(amount);

  if (
    !Number.isFinite(numericAmount) ||
    numericAmount < 0
  ) {
    throw new Error(
      "Amount must be a valid positive number."
    );
  }

  return numericAmount;
};

/**
 * ============================================================
 * GET USD → RWF
 * ============================================================
 */

const getUsdToRwfRate = async () => {
  return await exchangeRateService.getUsdToRwfRate();
};

/**
 * ============================================================
 * GET RWF → USD
 * ============================================================
 */

const getRwfToUsdRate = async () => {
  const usdToRwf =
    await getUsdToRwfRate();

  if (!usdToRwf || usdToRwf <= 0) {
    throw new Error(
      "Invalid USD to RWF exchange rate."
    );
  }

  return 1 / usdToRwf;
};

/**
 * ============================================================
 * GET ASSET → USD RATE
 * ============================================================
 *
 * Returns:
 *
 * 1 asset = X USD
 *
 * IMPORTANT:
 *
 * USD     = 1
 * USDT    = 1
 * USDC    = 1
 *
 * BTC requires a real BTC/USD market rate.
 */

const getToUsdRate = async (currency) => {
  const normalized =
    normalizeCurrency(currency);

  if (
    normalized === "USD" ||
    normalized === "USDT" ||
    normalized === "USDC"
  ) {
    return 1;
  }

  if (normalized === "RWF") {
    return await getRwfToUsdRate();
  }

  if (normalized === "BTC") {
    throw new Error(
      "BTC/USD exchange rate provider is not configured yet."
    );
  }

  throw new Error(
    `USD conversion unavailable for ${normalized}.`
  );
};

/**
 * ============================================================
 * CONVERT TO USD
 * ============================================================
 */

const convertToUsd = async (
  amount,
  currency
) => {
  const numericAmount =
    validateAmount(amount);

  const normalized =
    normalizeCurrency(currency);

  const rate =
    await getToUsdRate(normalized);

  return Number(
    (
      numericAmount * rate
    ).toFixed(2)
  );
};

/**
 * ============================================================
 * CONVERT USD → TARGET CURRENCY
 * ============================================================
 */

const convertFromUsd = async (
  usdAmount,
  targetCurrency
) => {
  const amount =
    validateAmount(usdAmount);

  const currency =
    normalizeCurrency(
      targetCurrency
    );

  if (
    currency === "USD" ||
    currency === "USDT" ||
    currency === "USDC"
  ) {
    return Number(
      amount.toFixed(2)
    );
  }

  if (currency === "RWF") {
    const rate =
      await getUsdToRwfRate();

    return Number(
      (
        amount * rate
      ).toFixed(2)
    );
  }

  if (currency === "BTC") {
    throw new Error(
      "USD/BTC conversion is not configured yet."
    );
  }

  throw new Error(
    `Conversion from USD to ${currency} is unavailable.`
  );
};

/**
 * ============================================================
 * CONVERT BETWEEN TWO CURRENCIES
 * ============================================================
 *
 * Example:
 *
 * convert(100000, "RWF", "USD")
 *
 * convert(100, "USD", "RWF")
 */

const convert = async (
  amount,
  fromCurrency,
  toCurrency
) => {
  const numericAmount =
    validateAmount(amount);

  const from =
    normalizeCurrency(
      fromCurrency
    );

  const to =
    normalizeCurrency(
      toCurrency
    );

  if (from === to) {
    return Number(
      numericAmount.toFixed(2)
    );
  }

  const usdAmount =
    await convertToUsd(
      numericAmount,
      from
    );

  return await convertFromUsd(
    usdAmount,
    to
  );
};

/**
 * ============================================================
 * GET USD EQUIVALENT OF WALLET
 * ============================================================
 *
 * The actual wallet balances are NOT changed.
 *
 * Example:
 *
 * USD  = $50
 * USDT = $30
 * USDC = $20
 *
 * USD equivalent = $100
 */

const getWalletUsdEquivalent =
  async (wallet) => {
    if (!wallet) {
      throw new Error(
        "Wallet is required."
      );
    }

    const usd =
      Number(
        wallet.usd?.balance || 0
      );

    const usdt =
      Number(
        wallet.crypto?.usdt?.balance ||
          0
      );

    const usdc =
      Number(
        wallet.crypto?.usdc?.balance ||
          0
      );

    const rwf =
      Number(
        wallet.rwf?.balance || 0
      );

    let totalUsd = 0;

    totalUsd +=
      await convertToUsd(
        usd,
        "USD"
      );

    totalUsd +=
      await convertToUsd(
        usdt,
        "USDT"
      );

    totalUsd +=
      await convertToUsd(
        usdc,
        "USDC"
      );

    totalUsd +=
      await convertToUsd(
        rwf,
        "RWF"
      );

    /**
     * BTC is intentionally not included
     * until BTC/USD pricing is configured.
     */

    return Number(
      totalUsd.toFixed(2)
    );
  };

/**
 * ============================================================
 * EXPORT
 * ============================================================
 */

export default {
  SUPPORTED_CURRENCIES,
  normalizeCurrency,
  getUsdToRwfRate,
  getRwfToUsdRate,
  getToUsdRate,
  convertToUsd,
  convertFromUsd,
  convert,
  getWalletUsdEquivalent,
};