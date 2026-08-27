import type { UserRole } from "@/app/lib/types";

export interface Account {
  id: string;
  email: string;
  phone: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Authorization {
  roles: string[];
  permissions: string[];
}

export interface AuthUser extends Account {
  role: UserRole;
  roles: string[];
  permissions: string[];
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  phone?: string;
  password: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
