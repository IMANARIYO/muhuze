export interface WalletTransaction {
  id: string;

  userId: string;

  type:
    | "deposit"
    | "withdraw"
    | "premium"
    | "referral"
    | "featured"
    | "advertising"
    | "upload";

  amount: number;

  description: string;

  status:
    | "pending"
    | "completed"
    | "failed";

  createdAt: string;
}

export interface Wallet {
  userId: string;

  balance: number;

  pendingBalance: number;

  totalEarned: number;

  totalWithdrawn: number;

  transactions: WalletTransaction[];
}