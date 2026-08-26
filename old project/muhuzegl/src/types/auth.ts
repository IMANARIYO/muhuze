import type { User } from "./user";

export interface LoginData {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface RegisterData {
  fullName: string;
  email: string;
  phone: string;
  password: string;
  confirmPassword: string;

  /**
   * User ID of the person who referred this new user.
   *
   * This comes from:
   *
   * /register?ref=USER_ID
   */
  referralCode?: string;

  acceptTerms: boolean;
}

export interface ForgotPasswordData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface AuthContextType {
  currentUser: User | null;

  login: (
    data: LoginData
  ) => boolean;

  logout: () => void;

  register: (
    data: RegisterData
  ) => boolean;
}