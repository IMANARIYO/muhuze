export interface ReferralCommission {
  id: string;

  referrerId: string;

  referredUserId: string;

  service: string;

  amount: number;

  percentage: number;

  status:
    | "pending"
    | "paid";

  createdAt: string;
}

export interface ReferralStats {
  totalReferrals: number;

  activeReferrals: number;

  totalCommission: number;

  pendingCommission: number;
}