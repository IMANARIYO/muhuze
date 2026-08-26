export interface ReferralUser {
  _id: string;
  fullName: string;
  email: string;
  username?: string;
}

export interface Referral {
  _id: string;

  referrer: string;

  referredUser: ReferralUser;

  referralCode: string;

  reward: number;

  status:
    | "Pending"
    | "Completed";

  createdAt: string;

  updatedAt: string;
}

export interface ReferralContextType {
  referralCode: string;

  referralLink: string;

  referrals: Referral[];

  totalReferrals: number;

  totalRewards: number;

  addReferral: (
    referredUser: string
  ) => Promise<void>;
}