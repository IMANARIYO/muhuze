export type PaymentService =
  | "premium-monthly"
  | "premium-annual"
  | "upload-fee"
  | "featured-product"
  | "advertising";

export interface PaymentTransaction {
  id: number;

  userId: string;

  service: PaymentService;

  amount: number;

  commission: number;

  status:
    | "pending"
    | "completed"
    | "failed";

  createdAt: string;
}