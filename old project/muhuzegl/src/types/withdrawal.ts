export type WithdrawalStatus =
  | "Pending"
  | "Processing"
  | "Completed"
  | "Rejected"
  | "Cancelled";

/**
 * ==========================================
 * POPULATED USER
 * ==========================================
 */

export interface WithdrawalUser {
  _id: string;
  fullName: string;
  email?: string;
  phone?: string;
}

/**
 * ==========================================
 * WITHDRAWAL
 * ==========================================
 */

export interface Withdrawal {
  _id: string;

  /**
   * Can be:
   *
   * 1. User ID string
   * 2. Populated user object
   */
  userId: string | WithdrawalUser;

  requestedAmount: number;

  feeRate: number;

  feeAmount: number;

  netAmount: number;

  currency: string;

  paymentMethod:
    | "MTN_MOBILE_MONEY"
    | "AIRTEL_MONEY"
    | "BANK_TRANSFER"
    | "USDT"
    | "USDC";

  network?: string;

  accountNumber: string;

  accountName?: string;

  status: WithdrawalStatus;

  processedAt?: string;

  processedBy?: string;

  rejectionReason?: string;

  walletTransactionId?: string;

  description?: string;

  createdAt: string;

  updatedAt: string;
}