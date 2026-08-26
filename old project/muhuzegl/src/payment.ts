export type ServiceType =
  | "premium-monthly"
  | "premium-annual"
  | "upload-fee"
  | "featured-product"
  | "advertising-starter"
  | "advertising-standard"
  | "advertising-premium";

export interface PaymentRequest {
  userId: string;

  service: ServiceType;

  amount: number;

  referredBy?: string;
}

export interface PaymentResult {
  success: boolean;

  message: string;

  commission: number;
}