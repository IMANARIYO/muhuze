export type WalletTransactionType =
  | "REFERRAL_COMMISSION"
  | "COMMISSION_REVERSAL"
  | "WITHDRAWAL"
  | "REFUND"
  | "ADJUSTMENT";

export type WalletTransactionStatus =
  | "Pending"
  | "Completed"
  | "Reversed"
  | "Cancelled";

/**
 * ==========================================
 * POPULATED USER
 * ==========================================
 */

export interface WalletTransactionUser {
  _id: string;
  fullName: string;
  email?: string;
  phone?: string;
}

/**
 * ==========================================
 * WALLET TRANSACTION
 * ==========================================
 */

export interface WalletTransaction {
  _id: string;

  userId:
    | string
    | WalletTransactionUser;

  type: WalletTransactionType;

  amount: number;

  currency: string;

  referenceId?: string;

  referenceType?:
    | "ReferralCommission"
    | "Withdrawal"
    | "RevenueTransaction"
    | "Order";

  status: WalletTransactionStatus;

  description?: string;

  createdAt: string;

  updatedAt: string;
}