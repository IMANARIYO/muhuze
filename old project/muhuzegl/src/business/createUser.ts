import type { User } from "../types/user";
import { generateReferralCode } from "../utils/generateReferralCode";

interface CreateUserInput {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  referredBy?: string;
}

export function createUser(
  data: CreateUserInput
): User {
  return {
    _id: crypto.randomUUID(),
    

    fullName: data.fullName,

    email: data.email,

    phone: data.phone,

    password: data.password,

    // Every new account starts as a buyer
    role: "buyer",

    status: "active",

    profileImage: "",

    bio: "",

    country: "Rwanda",

    province: "",

    district: "",

    sector: "",

    isEmailVerified: false,

    isPhoneVerified: false,

    sellerVerified: false,

    referralCode: generateReferralCode(
      data.fullName
    ),

    referredBy: data.referredBy,

    walletId: crypto.randomUUID(),

    premium: {
      active: false,

      plan: null,

      startDate: "",

      expiryDate: "",
    },

    createdAt: new Date().toISOString(),

    updatedAt: new Date().toISOString(),
  };
}