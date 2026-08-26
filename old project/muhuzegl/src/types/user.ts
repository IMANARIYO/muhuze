import type { PremiumSubscription } from "./premium";

export type UserRole =
  | "buyer"
  | "seller"
  | "admin";

export type UserStatus =
  | "active"
  | "pending"
  | "suspended";

export interface User {
  _id: string;

  fullName: string;

  email: string;

  phone: string;

  role: UserRole;

  createdAt: string;

  updatedAt: string;

  // Account status
  status?: UserStatus;

  // Authentication
  password?: string;

  // Profile
  profileImage?: string;
  bio?: string;

  // Rwanda location
  country?: string;
  province?: string;
  district?: string;
  sector?: string;
  cell?: string;
  village?: string;

  // Rwanda location IDs
  provinceId?: string;
  districtId?: string;
  sectorId?: string;
  cellId?: string;
  villageId?: string;

  // Verification
  isEmailVerified?: boolean;
  isPhoneVerified?: boolean;
  sellerVerified?: boolean;

  // Referral
  referralCode?: string;
  referredBy?: string;

  // Wallet
  walletId?: string;

  // Premium
  premium: PremiumSubscription;
}