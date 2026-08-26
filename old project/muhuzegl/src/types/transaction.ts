export type TransactionType =
  | "premium"
  | "upload"
  | "featured"
  | "advertising"
  | "withdraw"
  | "deposit";

export type TransactionStatus =
  | "pending"
  | "completed"
  | "failed";

export interface Transaction {
  id: string;

  userId: string;

  type: TransactionType;

  amount: number;

  description: string;

  status: TransactionStatus;

  createdAt: string;
}