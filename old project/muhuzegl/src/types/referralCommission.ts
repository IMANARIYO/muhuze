export type ReferralCommissionStatus =
  | "Pending"
  | "Available"
  | "Reversed"
  | "Cancelled";

export interface ReferralCommissionUser {
  _id: string;
  fullName: string;
  email: string;
  username?: string;
}

export interface ReferralCommission {
  _id: string;

  referrer: string;

  referredUser:
    | string
    | ReferralCommissionUser;

  revenueTransaction: string;

  sourceType: string;

  level: 1 | 2 | 3;

  commissionRate: number;

  revenueAmount: number;

  referralPoolAmount: number;

  commissionAmount: number;

  currency: string;

  status: ReferralCommissionStatus;

  availableAt: string;

  description: string;

  createdAt: string;

  updatedAt: string;
}

export interface ReferralCommissionSummary {
  totalCommission: number;

  pendingCommission: number;

  availableCommission: number;

  reversedCommission: number;

  cancelledCommission: number;
}