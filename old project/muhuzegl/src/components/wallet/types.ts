export interface WalletTransaction {
  id: string;

  type:
    | "REFERRAL_COMMISSION"
    | "COMMISSION_REVERSAL"
    | "WITHDRAWAL"
    | "REFUND"
    | "ADJUSTMENT";

  amount: number;

  currency: string;

  status:
    | "Pending"
    | "Completed"
    | "Reversed"
    | "Cancelled";

  description: string;

  date: string;

  referenceId?: string;

  referenceType?:
    | "ReferralCommission"
    | "Withdrawal"
    | "RevenueTransaction"
    | "Order";
}

/**
 * ==========================================
 * WALLET CONTEXT
 * ==========================================
 */

export interface WalletContextType {
  /**
   * Available wallet balance
   */
  balance: number;

  /**
   * Money waiting to become available
   */
  pendingBalance: number;

  /**
   * Lifetime earnings
   */
  totalEarned: number;

  /**
   * Lifetime withdrawals
   */
  totalWithdrawn: number;
  currency: string;
  /**
   * Wallet transactions
   */
  transactions: WalletTransaction[];

  /**
   * Loading state
   */
  loading: boolean;

  /**
   * Reload wallet from backend
   */
  refreshWallet: () => Promise<void>;

  /**
   * ==========================================
   * LEGACY METHODS
   * ==========================================
   *
   * These remain temporarily so existing
   * components don't immediately break.
   *
   * Real financial operations should be
   * handled by the backend.
   */

  deposit: (
    amount: number,
    description?: string
  ) => boolean;

  withdraw: (
    amount: number,
    description?: string
  ) => boolean;

  addSale: (
    amount: number,
    description?: string
  ) => boolean;

  addReferralReward: (
    amount: number,
    description?: string
  ) => boolean;
}