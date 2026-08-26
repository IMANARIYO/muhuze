import { apiClient } from "./apiClient";

/**
 * ==========================================
 * CREATE PREMIUM PAYMENT REQUEST
 * ==========================================
 */

export interface CreatePremiumPaymentRequest {
  plan: "Monthly" | "Annual";

  cryptoCurrency:
    | "USDT"
    | "USDC";

  cryptoNetwork:
    | "BEP20"
    | "ERC20";
}

/**
 * ==========================================
 * PAYMENT DOCUMENT
 * ==========================================
 */

export interface PremiumPayment {
  _id: string;

  userId: string;

  sourceId: string;

  sourceType: "PREMIUM";

  usdAmount: number;

  paymentMethod: "CRYPTO";

  cryptoCurrency:
    | "USDT"
    | "USDC";

  cryptoNetwork:
    | "BEP20"
    | "ERC20";

  cryptoAmount?: number;

  walletAddress?: string;

  transactionHash?: string;

  provider: "NOWPAYMENTS";

  providerPaymentId?: string;

  status:
    | "Pending"
    | "Processing"
    | "PartiallyPaid"
    | "Confirmed"
    | "Failed"
    | "Cancelled"
    | "Refunded";

  confirmedAt?: string;

  refundedAt?: string;

  createdAt: string;

  updatedAt: string;
}

/**
 * ==========================================
 * NOWPAYMENTS CHECKOUT INFORMATION
 * ==========================================
 */

export interface NowPaymentsCheckout {
  paymentId: string;

  payAddress?: string;

  payAmount?: number;

  payCurrency?: string;

  paymentStatus?: string;

  expirationEstimate?: string;
}

/**
 * ==========================================
 * PREMIUM SUBSCRIPTION
 * ==========================================
 */

export interface PremiumSubscriptionResponse {
  _id: string;

  userId: string;

  plan:
    | "Monthly"
    | "Annual";

  paymentId:
    | string
    | PremiumPayment
    | null;

  priceUsd: number;

  startDate:
    | string
    | null;

  expiryDate:
    | string
    | null;

  status:
    | "Pending"
    | "Active"
    | "Expired"
    | "Cancelled";

  sellerCommissionRate: number;

  referralCommissionEligible: boolean;

  activatedAt:
    | string
    | null;

  expiredAt:
    | string
    | null;

  cancelledAt:
    | string
    | null;

  cancellationReason?: string;

  createdAt: string;

  updatedAt: string;
}

/**
 * ==========================================
 * PAYMENT RESULT
 * ==========================================
 */

export interface PremiumPaymentResult {
  payment: PremiumPayment;

  provider: NowPaymentsCheckout;
}

/**
 * ==========================================
 * CREATE PREMIUM PAYMENT RESPONSE
 * ==========================================
 */

export interface CreatePremiumPaymentResponse {
  success: boolean;

  message: string;

  data: {
    subscription:
      PremiumSubscriptionResponse;

    payment:
      PremiumPaymentResult;
  };
}

/**
 * ==========================================
 * PREMIUM API SERVICE
 * ==========================================
 */

class PremiumApiService {


  /**
   * ========================================
   * CREATE PREMIUM PAYMENT
   * ========================================
   */

  async createPremiumPayment(
    data: CreatePremiumPaymentRequest
  ): Promise<CreatePremiumPaymentResponse> {

    return apiClient.post<CreatePremiumPaymentResponse>(
      "/premium",
      data
    );
  }

  /**
   * ========================================
   * GET CURRENT PREMIUM
   * ========================================
   */

  async getMyPremium(): Promise<{
    success: boolean;

    data:
      | PremiumSubscriptionResponse
      | null;
  }> {

    return apiClient.get(
      "/premium/me"
    );
  }

  /**
   * ========================================
   * GET PREMIUM HISTORY
   * ========================================
   */

  async getPremiumHistory(): Promise<{
    success: boolean;

    count: number;

    data:
      PremiumSubscriptionResponse[];
  }> {

    return apiClient.get(
      "/premium/history"
    );
  }
    /**
   * ==========================================
   * CANCEL PENDING PREMIUM PAYMENT
   * ==========================================
   */

  async cancelPendingPremium(): Promise<{
    success: boolean;
    message: string;
    data: PremiumSubscriptionResponse;
  }> {
    return apiClient.post(
      "/premium/pending/cancel"
    );
  }
  /**
 * ==========================================
 * CHECK LIVE PAYMENT STATUS
 * ==========================================
 */

async checkPaymentStatus(
  paymentId: string
): Promise<{
  success: boolean;
  message: string;
  data: PremiumPaymentResult;
}> {
  return apiClient.get(
    `/payments/${paymentId}/status`
  );
}
}

export const premiumApiService =
  new PremiumApiService();